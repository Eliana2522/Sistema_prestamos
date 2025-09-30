import os
import django
import sys

# Add the project path to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'prestamos_project')))

# Set up the Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from gestion_prestamos.models import Prestamo

def check_loan_data():
    print("--- Checking loan data integrity ---")
    
    problematic_loans = []
    all_loans = Prestamo.objects.all()
    
    if not all_loans.exists():
        print("No loans found in the database.")
        return

    for loan in all_loans:
        if loan.monto is None:
            problematic_loans.append(f"Loan with ID {loan.id} has a None amount.")
        elif loan.monto == 0:
            problematic_loans.append(f"Loan with ID {loan.id} has an amount of 0.")

    if problematic_loans:
        print("Found loans with problematic data:")
        for problem in problematic_loans:
            print(problem)
    else:
        print("All loans have a valid amount.")

    print("--- Data check complete ---")

if __name__ == "__main__":
    check_loan_data()
