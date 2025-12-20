# Cloudinary Configuration for Avatars

## Steps to configure Cloudinary

### 1. Create a Cloudinary account
1. Go to https://cloudinary.com/
2. Create a free account
3. In the dashboard, you will find your credentials:
   - Cloud Name
   - API Key
   - API Secret

### 2. Configure environment variables
Create a `.env` file in the project root with the following variables:

```env
# Cloudinary Configuration
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret
```

### 3. Apply migrations
```bash
python manage.py migrate
```

### 4. Implemented Key Features

#### User Model
- `avatar` field added as ImageField
- `avatar_url` property that returns the avatar URL or a default image
- Automatic storage in Cloudinary

#### Admin Panel
- List view shows avatar thumbnail
- Avatar field in the edit form
- Automatic image transformation (300x300px, crop: fill, gravity: face)

#### Cloudinary Configuration
- Automatic transformations to optimize images
- Global CDN for better performance
- Support for formats: jpg, jpeg, png, gif, webp

### 5. Usage in code

```python
# Get avatar URL
user = User.objects.get(id=1)
avatar_url = user.avatar_url

# Check if user has avatar
if user.avatar:
    print("User has avatar")
```

### 6. Free plan limits
- 25 GB of storage
- 25 GB of bandwidth per month
- Unlimited transformations
- Global CDN

## Important notes
- Images are automatically uploaded to Cloudinary when a user is saved
- Transformations are applied automatically to optimize performance
- The avatar field is optional (blank=True, null=True)
