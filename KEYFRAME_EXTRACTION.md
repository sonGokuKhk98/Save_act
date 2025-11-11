# How Keyframe Extraction Works by Duration

## 🎯 The Key: FFmpeg `fps` Filter

The magic happens in this line:

```python
"-vf", f"fps=1/{interval_seconds}",
```

## 📐 How It Works

### The FFmpeg Command

```python
# video_segmenter.py line 68-75
cmd = [
    "ffmpeg",
    "-i", str(video_path),              # Input video
    "-vf", f"fps=1/{interval_seconds}", # ← THIS IS THE KEY!
    "-q:v", "2",                        # High quality
    output_pattern,                      # Output pattern
    "-y"                                # Overwrite
]
```

### What `fps=1/3` Means

**`fps=1/3`** = **"1 frame per 3 seconds"**

This tells FFmpeg:
- Extract **1 frame every 3 seconds** throughout the entire video
- FFmpeg automatically handles the video duration
- It processes the video from start to end

## 📊 Example Calculation

### For a 30-second video with `interval_seconds=3`:

```
Video Timeline:
0s ──── 3s ──── 6s ──── 9s ──── 12s ──── 15s ──── 18s ──── 21s ──── 24s ──── 27s ──── 30s
│       │       │       │       │        │        │        │        │        │        │
Frame1  Frame2  Frame3  Frame4  Frame5   Frame6   Frame7   Frame8   Frame9   Frame10  Frame11
```

**Result**: 11 keyframes extracted (one at each 3-second mark)

### Formula:
```
Number of keyframes = (video_duration_seconds / interval_seconds) + 1
```

For 30-second video with 3-second interval:
- `(30 / 3) + 1 = 11 keyframes`

## 🔍 Step-by-Step Process

### 1. **Configuration** (line 57-58)
```python
if interval_seconds is None:
    interval_seconds = Config.KEYFRAME_INTERVAL_SECONDS  # Default: 3 seconds
```

### 2. **FFmpeg Filter Setup** (line 71)
```python
"-vf", f"fps=1/{interval_seconds}"
# If interval_seconds = 3, this becomes: "fps=1/3"
```

### 3. **FFmpeg Execution** (line 77-82)
```python
subprocess.run([
    "ffmpeg",
    "-i", "video.mp4",        # Input: video file
    "-vf", "fps=1/3",         # Filter: 1 frame per 3 seconds
    "keyframe_%04d.jpg",      # Output: keyframe_0001.jpg, keyframe_0002.jpg, ...
    "-y"
])
```

### 4. **What FFmpeg Does Internally**

FFmpeg:
1. **Reads the video** from start to end
2. **Calculates timestamps**: 0s, 3s, 6s, 9s, 12s, ...
3. **Extracts frame** at each timestamp
4. **Saves as image**: keyframe_0001.jpg, keyframe_0002.jpg, etc.

## 📝 Code Flow

```python
# video_segmenter.py line 42
def extract_keyframes(self, video_path: Path, interval_seconds: int = 3):
    # Step 1: Get interval from config if not provided
    if interval_seconds is None:
        interval_seconds = Config.KEYFRAME_INTERVAL_SECONDS  # 3 seconds
    
    # Step 2: Create output directory
    keyframe_dir = get_temp_file_path(f"keyframes_{video_path.stem}")
    output_pattern = str(keyframe_dir / "keyframe_%04d.jpg")
    
    # Step 3: Build FFmpeg command
    cmd = [
        "ffmpeg",
        "-i", str(video_path),                    # Input video
        "-vf", f"fps=1/{interval_seconds}",        # ← Extract 1 frame per N seconds
        "-q:v", "2",                              # Quality setting
        output_pattern,                           # Output pattern
        "-y"
    ]
    
    # Step 4: Execute FFmpeg
    subprocess.run(cmd, ...)  # ← FFmpeg does the work
    
    # Step 5: Find all extracted files
    keyframe_files = sorted(keyframe_dir.glob("keyframe_*.jpg"))
    return keyframe_files, None
```

## 🎬 FFmpeg `fps` Filter Explained

### Syntax: `fps=1/N`

- **`fps`**: Frames per second filter
- **`1/N`**: Extract 1 frame every N seconds
- **Example**: `fps=1/3` = 1 frame every 3 seconds = 0.33 fps

### How FFmpeg Calculates It

FFmpeg doesn't need to know the video duration upfront. It:
1. Processes video frame by frame
2. Tracks elapsed time
3. Extracts frame when `elapsed_time % interval == 0`
4. Continues until video ends

### Example Timeline

For a **45-second video** with **3-second interval**:

```
Time:  0s    3s    6s    9s    12s   15s   18s   21s   24s   27s   30s   33s   36s   39s   42s   45s
       │     │     │     │     │     │     │     │     │     │     │     │     │     │     │     │
Frame: 1     2     3     4     5     6     7     8     9     10    11    12    13    14    15    16
```

**Result**: 16 keyframes (one every 3 seconds)

## ⚙️ Configuration

### Default Setting
```python
# src/utils/config.py line 29
KEYFRAME_INTERVAL_SECONDS: int = int(os.getenv("KEYFRAME_INTERVAL_SECONDS", "3"))
```

### Change Interval

**In `.env` file:**
```bash
KEYFRAME_INTERVAL_SECONDS=5  # Extract 1 frame every 5 seconds (fewer frames)
KEYFRAME_INTERVAL_SECONDS=2  # Extract 1 frame every 2 seconds (more frames)
```

### Trade-offs

| Interval | Frames (30s video) | Speed | Quality |
|----------|-------------------|-------|---------|
| 1 second | 31 frames | Slower | Best |
| 3 seconds | 11 frames | Medium | Good (default) |
| 5 seconds | 7 frames | Faster | Lower |

## 🔧 How FFmpeg Knows Video Duration

FFmpeg **doesn't need to know duration upfront**. It:

1. **Reads video metadata** (duration is in video header)
2. **Processes sequentially** from start to end
3. **Extracts at intervals** as it goes
4. **Stops automatically** when video ends

The `fps` filter handles this automatically - you just specify the interval!

## 📋 Summary

**Question**: How does it know which keyframes to extract by duration?

**Answer**: 
- FFmpeg's `fps=1/N` filter extracts **1 frame every N seconds**
- FFmpeg automatically processes the **entire video** from start to end
- It extracts frames at: 0s, Ns, 2Ns, 3Ns, ... until video ends
- **No need to calculate duration** - FFmpeg handles it automatically!

**Code**: `video_segmenter.py` line 71: `fps=1/{interval_seconds}`

