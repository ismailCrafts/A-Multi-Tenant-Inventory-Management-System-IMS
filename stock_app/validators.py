from decimal import Decimal


# ==========================================================
# COMMON ITEM VALIDATION
# ==========================================================
def validate_items(product_ids, quantities, unit_prices):
    """
    Validate lists of product IDs, quantities, and unit prices.

    Steps:
    1. Ensure all lists are the same length.
    2. Loop through each row:
       - Check that product, quantity, and price are present.
       - Convert quantity and price to Decimal (catch errors).
       - Ensure quantity > 0 and price >= 0.
    3. Return (True, None) if all rows are valid, else (False, error message).
    """
    # Step 1: Length check
    if not (len(product_ids) == len(quantities) == len(unit_prices)):
        return False, "Product, quantity, and price lists must match in length."

    # Step 2: Row-by-row validation
    for i in range(len(product_ids)):
        # Step 2a: Required fields
        if not product_ids[i] or not quantities[i] or not unit_prices[i]:
            return False, f"Missing product, quantity, or price in row {i+1}."

        # Step 2b: Numeric conversion
        try:
            qty = Decimal(quantities[i])
            price = Decimal(unit_prices[i])
        except:
            return False, f"Invalid numeric value at row {i+1}."

        # Step 2c: Value constraints
        if qty <= 0 or price < 0:
            return False, f"Invalid quantity or price at row {i+1}."

    # Step 3: Success
    return True, None


# ==========================================================
# OPENING STOCK VALIDATION
# ==========================================================
def validate_opening_stock(data):
    """
    Validate opening stock input.

    Steps:
    1. Ensure product is provided.
    2. Ensure stock quantity is provided.
    3. Convert stock to Decimal (catch errors).
    4. Ensure stock >= 0.
    5. Return (True, None) if valid, else (False, error message).
    """
    # Step 1: Product required
    if not data.get("product"):
        return False, "Product is required."

    # Step 2: Stock required
    if not data.get("stock"):
        return False, "Stock quantity is required."

    # Step 3: Numeric conversion + Step 4: Non-negative check
    try:
        stock = Decimal(data.get("stock"))
        if stock < 0:
            return False, "Stock cannot be negative."
    except:
        return False, "Invalid stock value."

    # Step 5: Success
    return True, None


# ==========================================================
# REJECT VALIDATION
# ==========================================================
def validate_reject(data):
    """
    Validate product reject input.

    Steps:
    1. Ensure product is provided.
    2. Ensure quantity is provided.
    3. Convert quantity to Decimal (catch errors).
    4. Ensure quantity > 0.
    5. Ensure reason is provided.
    6. Return (True, None) if valid, else (False, error message).
    """
    # Step 1: Product required
    if not data.get("product"):
        return False, "Product is required."

    # Step 2: Quantity required
    if not data.get("quantity"):
        return False, "Quantity is required."

    # Step 3: Numeric conversion + Step 4: Positive check
    try:
        qty = Decimal(data.get("quantity"))
        if qty <= 0:
            return False, "Quantity must be greater than zero."
    except:
        return False, "Invalid quantity value."

    # Step 5: Reason required
    if not data.get("reason"):
        return False, "Reason is required."

    # Step 6: Success
    return True, None
