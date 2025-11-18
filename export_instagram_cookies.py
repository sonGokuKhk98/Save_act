#!/usr/bin/env python3
"""
Helper script to export Instagram cookies from your browser.
Run this locally, then upload the generated instagram_cookies.txt to your production server.

Usage:
    python export_instagram_cookies.py

Requirements:
    - You must be logged into Instagram in Chrome
    - You'll need to approve macOS keychain access when prompted
"""

import sys
from pathlib import Path

try:
    import yt_dlp
except ImportError:
    print("❌ yt-dlp not found. Install it with: pip install yt-dlp")
    sys.exit(1)


def export_cookies():
    """Export Instagram cookies from Chrome to a text file."""
    output_file = Path(__file__).parent / 'instagram_cookies.txt'
    
    print("🍪 Exporting Instagram cookies from Chrome...")
    print("⚠️  You may be prompted to enter your Mac password to access Chrome's keychain.")
    print()
    
    ydl_opts = {
        'cookiesfrombrowser': ('chrome',),
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,
        'skip_download': True,
    }
    
    try:
        # Use a real Instagram URL to trigger cookie extraction
        test_url = 'https://www.instagram.com/reel/Cne60hWpOdO/'
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract cookies
            ydl.cookiejar.save(str(output_file), ignore_discard=True, ignore_expires=True)
        
        if output_file.exists() and output_file.stat().st_size > 0:
            print(f"✅ Cookies exported successfully to: {output_file}")
            print()
            
            # Read the cookies content
            cookies_content = output_file.read_text()
            
            print("📋 Next steps - Add to Render (Backend):")
            print("1. Go to https://dashboard.render.com")
            print("2. Select your service → Environment tab")
            print("3. Add a new environment variable:")
            print("   Key: INSTAGRAM_COOKIES")
            print("   Value: (paste the entire content below)")
            print()
            print("=" * 60)
            print(cookies_content)
            print("=" * 60)
            print()
            print("4. Click 'Save Changes' - Render will auto-redeploy")
            print()
            print("⚠️  SECURITY WARNING:")
            print("   - Keep this SECRET - it contains your Instagram login session")
            print("   - NEVER commit it to git (already in .gitignore)")
            print("   - Regenerate if you log out of Instagram")
        else:
            print("❌ Cookie export failed - file is empty or not created")
            print("Make sure you:")
            print("  1. Are logged into Instagram in Chrome")
            print("  2. Approved the macOS keychain access prompt")
            return False
            
    except Exception as e:
        print(f"❌ Error exporting cookies: {e}")
        print()
        print("Troubleshooting:")
        print("  - Make sure Chrome is installed")
        print("  - Make sure you're logged into Instagram in Chrome")
        print("  - Try closing Chrome and running this script again")
        return False
    
    return True


if __name__ == '__main__':
    success = export_cookies()
    sys.exit(0 if success else 1)

