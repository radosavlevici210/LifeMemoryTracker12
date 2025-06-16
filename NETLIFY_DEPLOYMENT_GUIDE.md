
# Netlify Deployment Guide

## Fixed Issues

### 1. Python Version Compatibility
- **Changed from**: Python 3.11 (unsupported)
- **Changed to**: Python 3.9 (fully supported by Netlify)
- **Files updated**: `runtime.txt`, `netlify.toml`

### 2. Removed All CORS Policies
- **Removed**: All CORS headers and policy restrictions
- **Result**: Open access without cross-origin restrictions
- **Files updated**: `serverless_wrapper.py`, `netlify/functions/app.py`

### 3. Optimized Dependencies
- **Reduced**: Package requirements to essential only
- **Optimized**: For faster cold starts on serverless
- **Files updated**: `netlify/functions/requirements.txt`

## Deployment Configuration

### Build Settings
```toml
[build]
  publish = "static"
  command = "python -m pip install --upgrade pip && pip install -r netlify/functions/requirements.txt"
  functions = "netlify/functions"

[build.environment]
  PYTHON_VERSION = "3.9"
  NODE_VERSION = "20"
```

### Environment Variables Required
Set these in Netlify dashboard:
- `OPENAI_API_KEY`: Your OpenAI API key
- `SESSION_SECRET`: Random secret for sessions

### Function Routes
All API routes redirect to `/.netlify/functions/app`:
- `/chat` - Main chat endpoint
- `/memory` - Memory management
- `/health` - Health checks
- `/login` - Authentication
- `/logout` - Logout

### Static Files
Frontend files served from `/static` directory:
- HTML templates
- CSS styles
- JavaScript files
- Service worker

## Deployment Steps

1. **Connect Repository**: Link your GitHub repo to Netlify
2. **Set Environment Variables**: Add required API keys
3. **Deploy**: Netlify will automatically build and deploy
4. **Test**: Verify all endpoints work correctly

## Performance Optimizations

- **Lazy Loading**: OpenAI client loaded only when needed
- **Memory Caching**: Reduced database calls
- **Minimal Dependencies**: Only essential packages
- **Fast Model**: Using GPT-4o-mini for faster responses
- **Optimized Tokens**: Reduced max tokens for speed

The deployment should now work without any CORS or policy restrictions.
