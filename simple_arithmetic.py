import tkinter as tk
from tkinter import messagebox

# -----------------------------
# FUNCTION TO CALCULATE RESULTS
# -----------------------------
def calculate():
    try:
        # Get input values
        a = float(entry_a.get())
        b = float(entry_b.get())

        # Perform operations
        add = a + b
        sub = a - b
        mul = a * b

        # Handle division safely
        if b != 0:
            div = a / b
        else:
            div = "Undefined (divide by zero)"

        # Display results
        result_text.set(
            f"Addition: {add}\n"
            f"Subtraction: {sub}\n"
            f"Multiplication: {mul}\n"
            f"Division: {div}"
        )

    except ValueError:
        messagebox.showerror("Input Error", "Please enter valid numbers!")

# -----------------------------
# MAIN WINDOW
# -----------------------------
root = tk.Tk()
root.title("Simple Arithmetic GUI")
root.geometry("350x250")

# Title label
title = tk.Label(root, text="=== SIMPLE ARITHMETIC ===", font=("Arial", 12, "bold"))
title.pack(pady=10)

# First number input
tk.Label(root, text="Enter first number:").pack()
entry_a = tk.Entry(root)
entry_a.pack()

# Second number input
tk.Label(root, text="Enter second number:").pack()
entry_b = tk.Entry(root)
entry_b.pack()

# Calculate button
calc_button = tk.Button(root, text="Calculate", command=calculate)
calc_button.pack(pady=10)

# Result display
result_text = tk.StringVar()
result_label = tk.Label(root, textvariable=result_text, justify="left", fg="blue")
result_label.pack()

# Run GUI loop
root.mainloop()
