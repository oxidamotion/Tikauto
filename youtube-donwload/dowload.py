from pytubefix import YouTube, Playlist
import os
from datetime import datetime
from moviepy.editor import VideoFileClip, CompositeVideoClip

# Helper Function: Download YouTube video
def download_video(url, output_folder):
    try:
        yt = YouTube(url)
        print(f"Downloading video: {yt.title}")
        stream = yt.streams.get_highest_resolution()
        video_path = stream.download(output_path=output_folder)
        print(f"Downloaded: {video_path}")
        return video_path
    except Exception as e:
        print(f"Error downloading video: {e}")
        return None

# Helper Function: Create a unique output folder
def create_output_folder(base_folder="output"):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder_name = f"{base_folder}_{timestamp}"
    os.makedirs(folder_name, exist_ok=True)
    return folder_name

# Helper Function: Adjust video durations
def adjust_video_durations(top_video, bottom_video):
    try:
        if bottom_video.duration < top_video.duration:
            print("Bottom video is shorter than top video. Looping the bottom video to match duration.")
            bottom_video = bottom_video.loop(duration=top_video.duration)
        return top_video, bottom_video
    except Exception as e:
        print(f"Error adjusting durations: {e}")
        return None, None

# Helper Function: Combine videos with one on top of the other
def stack_videos(top_video_path, bottom_video_path, output_path):
    try:
        top_clip = VideoFileClip(top_video_path)
        bottom_clip = VideoFileClip(bottom_video_path).without_audio()  # Remove audio from bottom video

        # Resize both clips to have the same width
        width = min(top_clip.w, bottom_clip.w)
        top_clip = top_clip.resize(width=width)
        bottom_clip = bottom_clip.resize(width=width)

        # Adjust durations
        top_clip, bottom_clip = adjust_video_durations(top_clip, bottom_clip)
        if not top_clip or not bottom_clip:
            print("Error adjusting video durations. Skipping this pair.")
            return None

        # Create a stacked composite
        stacked_clip = CompositeVideoClip([
            top_clip.set_position(("center", "top")),
            bottom_clip.set_position(("center", "bottom"))
        ], size=(width, top_clip.h + bottom_clip.h))

        # Write the output
        stacked_clip.write_videofile(output_path, codec="libx264", fps=30)
        print(f"Combined video saved to {output_path}")
        return output_path
    except Exception as e:
        print(f"Error combining videos: {e}")
        return None

# Helper Function: Split video into chunks of 1:15 (75 seconds)
def split_video(video_path, output_folder, chunk_duration=75):
    try:
        clip = VideoFileClip(video_path)
        total_duration = int(clip.duration)
        chunks = []
        
        for start_time in range(0, total_duration, chunk_duration):
            end_time = min(start_time + chunk_duration, total_duration)
            chunk = clip.subclip(start_time, end_time)
            chunk_path = os.path.join(output_folder, f"chunk_{start_time // chunk_duration + 1}.mp4")
            chunk.write_videofile(chunk_path, codec="libx264", fps=30)
            chunks.append(chunk_path)
            print(f"Saved chunk: {chunk_path}")
        
        return chunks
    except Exception as e:
        print(f"Error splitting video: {e}")
        return []

# Process a single pair of videos
def process_video_pair(top_video_url, bottom_video_url, output_folder):
    # Download videos
    top_video_path = download_video(top_video_url, output_folder)
    bottom_video_path = download_video(bottom_video_url, output_folder)

    if not top_video_path or not bottom_video_path:
        print("Failed to download one or both videos. Skipping.")
        return None

    # Combine videos
    combined_video_path = os.path.join(output_folder, "combined_video.mp4")
    stacked_video_path = stack_videos(top_video_path, bottom_video_path, combined_video_path)
    if not stacked_video_path:
        print("Failed to combine videos. Skipping.")
        return None

    # Split into chunks
    chunks_folder = os.path.join(output_folder, "chunks")
    os.makedirs(chunks_folder, exist_ok=True)
    split_video(stacked_video_path, chunks_folder)

# Function to process videos manually
def process_single_video():
    output_folder = create_output_folder()
    top_video_url = input("Enter the URL for the top video: ").strip()
    bottom_video_url = input("Enter the URL for the bottom video: ").strip()

    process_video_pair(top_video_url, bottom_video_url, output_folder)

# Function to process playlists
def process_playlists():
    output_folder = create_output_folder()
    top_playlist_url = input("Enter the URL for the top playlist: ").strip()
    bottom_playlist_url = input("Enter the URL for the bottom playlist: ").strip()

    top_playlist = Playlist(top_playlist_url)
    bottom_playlist = Playlist(bottom_playlist_url)

    print(f"Found {len(top_playlist.video_urls)} videos in top playlist.")
    print(f"Found {len(bottom_playlist.video_urls)} videos in bottom playlist.")

    # Pair videos and process them
    for top_url, bottom_url in zip(top_playlist.video_urls, bottom_playlist.video_urls):
        print(f"Processing pair: Top = {top_url}, Bottom = {bottom_url}")
        process_video_pair(top_url, bottom_url, output_folder)

# Main function with menu
def main():
    while True:
        print("\n--- YouTube Video Processor ---")
        print("1. Process a single pair of videos")
        print("2. Process playlists")
        print("3. Exit")
        choice = input("Select an option (1/2/3): ").strip()

        if choice == "1":
            process_single_video()
        elif choice == "2":
            process_playlists()
        elif choice == "3":
            print("Exiting.")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
