"""
Routes package for TheraGenie API

This package organizes API routes by domain. Routes are gradually being
migrated from the monolithic server.py to individual route modules.

Current status:
- Most routes are still in server.py
- Models extracted to models/__init__.py
- Auth utilities extracted to auth.py
- Database config extracted to database.py

Migration plan:
1. Phase 1 (current): Extract models, auth, database
2. Phase 2: Extract admin routes
3. Phase 3: Extract client routes
4. Phase 4: Extract therapist routes
5. Phase 5: Extract clinical routes (notes, assessments, protocols)
"""

# Routes will be imported here as they are migrated
