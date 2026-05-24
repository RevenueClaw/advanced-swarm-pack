# Calculation Verifier

Math reliability with step-by-step verification and Python execution.

## Quick Start

```python
from lib.calculation_verifier import CalculationVerifier

verifier = CalculationVerifier()

# Simple calculation
result = verifier.verify("12 * 5")
# Method: mental, Confidence: 95%

# Complex calculation
result = verifier.verify("(234 + 567) * 3 - 1200")
# Method: calculator, Steps: provided

# Force Python interpreter
result = verifier.verify("2.34 * 5.67", use_tool=True)
# Method: python, Confidence: 99%
```

## Complexity Levels

| Level | Method | Confidence |
|-------|--------|------------|
| Trivial | Mental | 98% |
| Simple | Mental | 95% |
| Moderate | Calculator | 90% |
| Complex | Python | 99% |
| Use Tool | Python | 99% |

## Integration with Architect-First

Calculations in subtask times are automatically verified during planning phase.

## Features

- **Automatic complexity detection**: Routes to appropriate method
- **Step-by-step reasoning**: Shows work clearly
- **Verification pass**: Double-checks result
- **Use Tool flag**: Force high-precision execution

## Warning Signs

The system escalates to Python for:
- Float operations (2.34 * 5.67)
- Large numbers (>999)
- Multiple operations (3+ operators)
- Complex expressions with precedence