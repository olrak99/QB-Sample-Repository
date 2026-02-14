"""
this is a long 
comment
testing

"""

# Simple Moment Calculator
# Formula: Moment = Force x Distance

print("=== MOMENT CALCULATOR ===")

# Ask user input
force = float(input("Enter Force (kN or N): "))
distance = float(input("Enter Distance (m): "))

# Calculate moment
moment = force * distance

# Display result
print("\nResult:")
print("Moment =", moment, "kN-m (or N-m depending on input units)")

#Changes Comment