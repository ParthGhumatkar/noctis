import sys
import traceback
from noctis import Noctis

if __name__ == "__main__":
    try:
        app = Noctis()
        app.mainloop()
    except Exception as e:
        print("\n" + "=" * 50)
        print("ERROR STARTING NOCTIS:")
        print("=" * 50)
        traceback.print_exc()
        print("=" * 50)
        input("\nPress Enter to close...")
