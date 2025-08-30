# Extension Icons

This directory should contain the following icon files for the browser extension:

## Required Icons

- `icon16.png` - 16x16 pixels (toolbar icon)
- `icon48.png` - 48x48 pixels (extension management page)
- `icon128.png` - 128x128 pixels (Chrome Web Store)

## Icon Design Guidelines

- Use a simple, recognizable design
- Ensure good contrast and visibility at small sizes
- Follow browser extension icon guidelines
- Use PNG format with transparency support

## Creating Icons

You can create these icons using any image editing software:

1. **Design the base icon** (recommended size: 128x128)
2. **Export at different sizes**:
   - 16x16 for toolbar
   - 48x48 for management page
   - 128x128 for store listing

## Placeholder Icons

For development, you can use simple placeholder icons or create basic ones with:

```bash
# Using ImageMagick (if available)
convert -size 16x16 xc:blue -fill white -draw "text 2,12 'W'" icon16.png
convert -size 48x48 xc:blue -fill white -draw "text 8,36 'W'" icon48.png
convert -size 128x128 xc:blue -fill white -draw "text 20,96 'W'" icon128.png
```

## Walmart Branding

For production, ensure icons follow Walmart's brand guidelines:
- Use Walmart blue (#0071ce)
- Include security/shield elements
- Maintain professional appearance 