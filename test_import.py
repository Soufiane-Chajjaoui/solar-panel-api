#!/usr/bin/env python3
try:
    from app.main import app
    print('main app imported successfully')
except Exception as e:
    print(f'Error importing main app: {e}')
    import traceback
    traceback.print_exc()