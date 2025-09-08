from django import template
from decimal import Decimal

register = template.Library()

@register.filter(name='format_number')
def format_number(value):
    try:
        # Ensure we have a number, default to 0
        if value is None:
            value = 0
        
        # Use f-string formatting to add commas, then replace them with dots
        # This is a robust way to handle integers and decimals
        formatted_value = f"{value:,.2f}"
        
        # Replace comma with a temp char, dot with comma, then temp char with dot
        # This correctly swaps them for Spanish-style formatting
        # e.g., 1,234.56 -> 1.234,56
        return formatted_value.replace(',', 'X').replace('.', ',').replace('X', '.')

    except (ValueError, TypeError):
        return value