
import os
from PIL import Image

# Setup Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..'))
BACKEND_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
FRONTEND_PUBLIC_DIR = os.path.join(ROOT_DIR, 'frontend', 'public')

MINI_LOGO_PATH = os.path.join(ROOT_DIR, 'mini-logo.jpeg')
BIG_LOGO_PATH = os.path.join(ROOT_DIR, 'big_logo.jpeg')



def make_transparent(img, tolerance=30):
    """
    Convert background to transparent by sampling the top-left pixel.
    """
    img = img.convert("RGBA")
    datas = img.getdata()
    
    # Sample the background color from top-left pixel
    bg_color = datas[0]
    
    new_data = []
    
    for item in datas:
        # Check if pixel is close to background color within tolerance
        if (abs(item[0] - bg_color[0]) <= tolerance and
            abs(item[1] - bg_color[1]) <= tolerance and
            abs(item[2] - bg_color[2]) <= tolerance):
            new_data.append((255, 255, 255, 0)) # Transparent
        else:
            new_data.append(item)
            
    img.putdata(new_data)
    return img

# Override the process functions to use make_transparent
def process_mini_logo():
    if not os.path.exists(MINI_LOGO_PATH):
        print(f"Error: {MINI_LOGO_PATH} not found.")
        return

    print(f"Processing {MINI_LOGO_PATH}...")
    try:
        img = Image.open(MINI_LOGO_PATH)
        img = make_transparent(img)
        
        # 1. Crop to square (Center crop)
        width, height = img.size
        size = min(width, height)
        left = (width - size) / 2
        top = (height - size) / 2
        right = (width + size) / 2
        bottom = (height + size) / 2
        
        img_square = img.crop((left, top, right, bottom))
        
        # 2. Resize and Save as logo-sm.png (512x512)
        img_512 = img_square.resize((512, 512), Image.Resampling.LANCZOS)
        out_path_sm = os.path.join(FRONTEND_PUBLIC_DIR, 'logo-sm.png')
        img_512.save(out_path_sm, format='PNG')
        print(f"Saved {out_path_sm}")

        # 3. Save as favicon.ico
        out_path_ico = os.path.join(FRONTEND_PUBLIC_DIR, 'favicon.ico')
        img_square.save(out_path_ico, format='ICO', sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
        print(f"Saved {out_path_ico}")
        
    except Exception as e:
        print(f"Failed to process mini-logo: {e}")

def process_big_logo():
    if not os.path.exists(BIG_LOGO_PATH):
        print(f"Error: {BIG_LOGO_PATH} not found.")
        return

    print(f"Processing {BIG_LOGO_PATH}...")
    try:
        img = Image.open(BIG_LOGO_PATH)
        img = make_transparent(img)
        
        # Resize to fixed height of 64px (header size roughly)
        target_height = 64
        aspect_ratio = img.width / img.height
        target_width = int(target_height * aspect_ratio)
        
        img_resized = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
        
        out_path_lg = os.path.join(FRONTEND_PUBLIC_DIR, 'logo-lg.png')
        img_resized.save(out_path_lg, format='PNG')
        print(f"Saved {out_path_lg}")
        
    except Exception as e:
        print(f"Failed to process big_logo: {e}")

if __name__ == "__main__":
    if not os.path.exists(FRONTEND_PUBLIC_DIR):
        print(f"Creating {FRONTEND_PUBLIC_DIR}...")
        os.makedirs(FRONTEND_PUBLIC_DIR, exist_ok=True)
        
    process_mini_logo()
    process_big_logo()
    print("Done.")
