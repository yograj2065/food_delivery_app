# Media Settings Fix - TODO Steps

## Plan Breakdown
1. ✅ Edit backend/backend/settings.py: Add `import os` and update MEDIA_ROOT to use os.path.join
2. ✅ Create media directory: `mkdir -p backend/media/products`
3. [ ] Test setup (upload image via admin, verify frontend display)

**Status:** Completed steps 1-2. ✅ All media configuration complete!

**Next:** 
- Restart Django server: `cd backend && python manage.py runserver`
- Go to http://127.0.0.1:8000/admin, login, add/edit Product with image upload
- Check frontend at http://localhost:3000 - images should display with full URLs from serializer

