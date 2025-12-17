"""Script para testar se as rotas de jobs estao sendo registradas"""
import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent))

print("Importando app...")
from factory.dashboard.app import app

print(f"Total de rotas: {len(app.routes)}")
print("\nRotas de jobs:")
for route in app.routes:
    if hasattr(route, 'path') and 'job' in route.path.lower():
        methods = getattr(route, 'methods', {'GET'})
        print(f"  {list(methods)[0]:6} {route.path}")

print("\nRotas de queue:")
for route in app.routes:
    if hasattr(route, 'path') and 'queue' in route.path.lower():
        methods = getattr(route, 'methods', {'GET'})
        print(f"  {list(methods)[0]:6} {route.path}")

print("\nRotas de workers:")
for route in app.routes:
    if hasattr(route, 'path') and 'worker' in route.path.lower():
        methods = getattr(route, 'methods', {'GET'})
        print(f"  {list(methods)[0]:6} {route.path}")
