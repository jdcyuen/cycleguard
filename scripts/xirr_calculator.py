
"""
xirr_calculator.py

Calculate the annualized return for investments with cash flows
that occur on different dates.

No third-party packages are required.

Cash-flow convention:
    Negative number = money invested
    Positive number = money received or ending portfolio value

https://chatgpt.com/c/69fa1b72-93b4-83e8-9306-47aab153f3be

"""

from datetime import date
from math import exp, isfinite, log


def xirr(cash_flows, dates, tolerance=1e-10, max_iterations=200):
    """
    Calculate XIRR and return it as a decimal.
    For example, 0.10 means a 10% annualized return.

    cash_flows: list of investment amounts
    dates:      list of matching datetime.date objects
    tolerance:  how close the calculation must get to zero
    max_iterations: maximum number of calculation attempts
    """

    # STEP 1: Validate the input.
    # Every cash flow must have a matching date.
    # At least two dated cash flows are needed.
    if len(cash_flows) != len(dates) or len(dates) < 2:
        raise ValueError(
            "Provide at least two matching cash flows and dates."
        )

    # Reject invalid numbers such as infinity or NaN.
    if not all(isfinite(float(cf)) for cf in cash_flows):
        raise ValueError("Cash flows must be finite numbers.")

    # XIRR needs both money invested and money received.
    # The ending portfolio value normally supplies the positive amount.
    if not any(cf < 0 for cf in cash_flows):
        raise ValueError("At least one cash flow must be negative.")

    if not any(cf > 0 for cf in cash_flows):
        raise ValueError("At least one cash flow must be positive.")

    # STEP 2: Sort cash flows by date.
    # The earliest date becomes day zero for the calculation.
    entries = sorted(
        zip(dates, cash_flows),
        key=lambda item: item[0]
    )

    start_date = entries[0][0]

    # Convert calendar dates into elapsed days:
    # day 0, day 31, day 59, and so on.
    days = [(d - start_date).days for d, _ in entries]

    # Keep the amounts in the same order as their dates.
    flows = [float(cf) for _, cf in entries]

    # Require the cash flows to span more than one day.
    if days[-1] == 0:
        raise ValueError("Cash flows must span more than one day.")

    # STEP 3: Calculate the net present value at a proposed rate.
    #
    # XIRR searches for the annual rate that makes this
    # function equal to zero.
    #
    # Each cash flow is discounted according to how many
    # days have elapsed since the first date.
    def npv(rate):
        # A rate <= -100% is invalid for this calculation.
        if rate <= -1:
            return float("inf")

        return sum(
            cf * exp(-day / 365.0 * log(1.0 + rate))
            for cf, day in zip(flows, days)
        )

    # STEP 4: Find a range of possible rates.
    #
    # Start by testing -99.9999% and +100%.
    # We need the NPV values at the two ends to have
    # opposite signs so that bisection can find a root.
    low = -0.999999
    high = 1.0

    f_low = npv(low)
    f_high = npv(high)

    # If the NPV has not changed sign, try higher rates.
    # For example: 100%, 300%, 700%, 1500%, etc.
    while f_low * f_high > 0 and high < 1e10:
        high = high * 2 + 1
        f_high = npv(high)

    # No bracket was found, so stop instead of returning
    # a potentially misleading result.
    if f_low * f_high > 0:
        raise ValueError(
            "Could not bracket an XIRR solution. "
            "The cash flows may have multiple or no real solutions."
        )

    # STEP 5: Use the bisection method to refine the rate.
    #
    # Test the midpoint between low and high.
    # Keep the half of the range where the NPV changes sign.
    # Repeating this narrows the range around the solution.
    for _ in range(max_iterations):
        mid = (low + high) / 2
        f_mid = npv(mid)

        # Stop when the NPV is close enough to zero
        # or the rate range is sufficiently narrow.
        if abs(f_mid) < tolerance or (high - low) < tolerance:
            return mid

        # Decide which half of the range contains the root.
        if f_low * f_mid <= 0:
            high = mid
            f_high = f_mid
        else:
            low = mid
            f_low = f_mid

    # If the calculation never met the stopping condition,
    # report failure instead of silently returning a result.
    raise ArithmeticError("XIRR did not converge.")


if __name__ == "__main__":
    # STEP 6: Example data.
    # These amounts and dates are illustrative, not actual account data.
    cash_flows = [
        -25000,  # Jan 5: first investment
        -20000,  # Feb 5: second investment
        -20000,  # Mar 5: third investment
         70000,  # Oct 2: ending portfolio value
    ]

    dates = [
        date(2026, 1, 5),
        date(2026, 2, 5),
        date(2026, 3, 5),
        date(2026, 10, 2),
    ]

    # STEP 7: Calculate XIRR using the function above.
    result = xirr(cash_flows, dates)

    # STEP 8: Display the results.
    # The percentage is annualized, not simply the total gain.
    print(f"Annualized XIRR: {result:.2%}")

    # The final positive cash flow represents the ending value.
    print(f"Ending value: ${cash_flows[-1]:,.2f}")

    # This is the simple dollar gain in this example:
    # $70,000 ending value - $65,000 invested = $5,000.
    print(f"Net gain: ${sum(cash_flows):,.2f}")
