"""
Pure Python .po to .mo compiler - no external tools needed.
Usage: python compile_po.py <path_to_po_file>
"""
import struct
import sys

def unescape(s):
    s = s.strip('"')
    s = s.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"').replace('\\\\', '\\')
    return s

def parse_po(po_path):
    entries = {}  # msgid -> msgstr (including empty msgid for header)
    current_msgid = None
    current_msgstr = None
    in_msgid = False
    in_msgstr = False

    def save():
        nonlocal current_msgid, current_msgstr
        if current_msgid is not None and current_msgstr is not None:
            entries[current_msgid] = current_msgstr
        current_msgid = None
        current_msgstr = None

    with open(po_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.rstrip('\r\n')

            if line.startswith('#~'):
                continue  # skip obsolete entries

            if line.startswith('#') or line.strip() == '':
                save()
                in_msgid = False
                in_msgstr = False
                continue

            if line.startswith('msgid '):
                save()
                current_msgid = unescape(line[6:].strip())
                current_msgstr = None
                in_msgid = True
                in_msgstr = False
            elif line.startswith('msgstr '):
                current_msgstr = unescape(line[7:].strip())
                in_msgid = False
                in_msgstr = True
            elif line.startswith('"'):
                val = unescape(line.strip())
                if in_msgid and current_msgid is not None:
                    current_msgid += val
                elif in_msgstr and current_msgstr is not None:
                    current_msgstr += val

    save()  # save last entry
    return entries

def compile_po_to_mo(po_path, mo_path):
    entries = parse_po(po_path)

    # Build header if missing
    if '' not in entries:
        entries[''] = (
            'Content-Type: text/plain; charset=UTF-8\n'
            'Content-Transfer-Encoding: 8bit\n'
            'Plural-Forms: nplurals=2; plural=(n != 1);\n'
        )

    # Keep only entries with non-empty msgstr (but always keep header)
    messages = {}
    for k, v in entries.items():
        if k == '' or v.strip():
            messages[k] = v

    # Sort: empty string (header) first, then alphabetical
    keys = sorted(messages.keys(), key=lambda x: (x != '', x))
    num = len(keys)

    encoded_keys   = [k.encode('utf-8') for k in keys]
    encoded_values = [messages[k].encode('utf-8') for k in keys]

    # MO layout:
    # 28 bytes header
    # num * 8 bytes: original string table  (length, offset)
    # num * 8 bytes: translation string table (length, offset)
    # string data

    strings_start = 28 + num * 8 * 2  # after both tables

    # Build offsets for original strings
    key_offsets = []
    pos = strings_start
    for ek in encoded_keys:
        key_offsets.append((len(ek), pos))
        pos += len(ek) + 1  # null terminated

    # Build offsets for translation strings
    val_offsets = []
    for ev in encoded_values:
        val_offsets.append((len(ev), pos))
        pos += len(ev) + 1

    with open(mo_path, 'wb') as f:
        # Magic (little-endian)
        f.write(struct.pack('<I', 0x950412de))
        # Revision
        f.write(struct.pack('<I', 0))
        # Number of strings
        f.write(struct.pack('<I', num))
        # Offset of original strings table
        f.write(struct.pack('<I', 28))
        # Offset of translation strings table
        f.write(struct.pack('<I', 28 + num * 8))
        # Hash table size (unused)
        f.write(struct.pack('<I', 0))
        # Hash table offset
        f.write(struct.pack('<I', 28 + num * 16))

        # Original strings table
        for length, offset in key_offsets:
            f.write(struct.pack('<II', length, offset))

        # Translation strings table
        for length, offset in val_offsets:
            f.write(struct.pack('<II', length, offset))

        # Original string data
        for ek in encoded_keys:
            f.write(ek + b'\x00')

        # Translation string data
        for ev in encoded_values:
            f.write(ev + b'\x00')

    print(f"Compiled {num} translations: {po_path} -> {mo_path}")

if __name__ == '__main__':
    po = sys.argv[1]
    mo = po.replace('.po', '.mo')
    compile_po_to_mo(po, mo)
