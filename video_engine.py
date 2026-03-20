"""
Moteur de generation video partage.
Gere l'animation de defilement de cartes en 3 colonnes.
"""
from moviepy.editor import CompositeVideoClip, ColorClip


def create_separator(width, height):
    return ColorClip(size=(width, height), color=(0, 0, 0))


def get_card_position(index, card_width, separator_width):
    if index == 0:
        return 0
    elif index == 1:
        return card_width + separator_width
    else:
        return (card_width + separator_width) * 2


def get_separator_position(index, card_width, separator_width):
    card_spacing = card_width + separator_width
    return card_width + (index * card_spacing)


def build_scrolling_video(all_cards, video_config):
    """
    Construit une video avec animation de defilement a partir d'une liste de cartes.

    video_config: dict avec les cles:
        width, height, separator_width, fps, scroll_duration,
        intro_duration, pause_duration, initial_delay,
        output_file, bitrate, preset, threads
    """
    WIDTH = video_config.get('width', 1920)
    HEIGHT = video_config.get('height', 1080)
    SEPARATOR_WIDTH = video_config.get('separator_width', 8)
    CARD_WIDTH = (WIDTH - SEPARATOR_WIDTH * 2) // 3
    CARD_HEIGHT = HEIGHT
    FPS = video_config.get('fps', 60)
    SCROLL_DURATION = video_config.get('scroll_duration', 3.6)
    INTRO_DURATION = video_config.get('intro_duration', 1.0)
    PAUSE_DURATION = video_config.get('pause_duration', 0.5)
    INITIAL_DELAY = video_config.get('initial_delay', 0.2)
    output_file = video_config.get('output_file', 'output.mp4')
    bitrate = video_config.get('bitrate', '4000k')
    preset = video_config.get('preset', 'medium')
    threads = video_config.get('threads', 4)

    clips = []

    # Phase 1: Introduction animation for first 3 cards
    for i in range(min(3, len(all_cards))):
        card = all_cards[i]
        final_x = get_card_position(i, CARD_WIDTH, SEPARATOR_WIDTH)

        def make_position(index, final_pos):
            def get_position(t):
                intro_start = index * INITIAL_DELAY
                relative_intro_t = t - intro_start
                if relative_intro_t < 0:
                    return (final_pos, -HEIGHT)
                elif t < INTRO_DURATION:
                    start_y = -HEIGHT
                    end_y = 0
                    progress = relative_intro_t / (INTRO_DURATION - (index * INITIAL_DELAY))
                    progress = min(1, progress)
                    eased_progress = 1 - (1 - progress) ** 2
                    return (final_pos, start_y + (end_y - start_y) * eased_progress)
                elif t < (INTRO_DURATION + PAUSE_DURATION):
                    return (final_pos, 0)
                else:
                    scroll_time = t - (INTRO_DURATION + PAUSE_DURATION)
                    speed = (WIDTH + CARD_WIDTH) / (SCROLL_DURATION * 4)
                    x = final_pos - (scroll_time * speed)
                    return (x, 0)
            return get_position

        intro_clip = card.set_position(make_position(i, final_x))
        intro_clip = intro_clip.set_start(0)
        intro_clip = intro_clip.set_duration(INTRO_DURATION + PAUSE_DURATION + SCROLL_DURATION * 3.5)
        clips.append(intro_clip)

        if i < 2:
            separator = create_separator(SEPARATOR_WIDTH, CARD_HEIGHT)
            separator_x = get_separator_position(i, CARD_WIDTH, SEPARATOR_WIDTH)

            def make_separator_position(index, sep_pos):
                def get_position(t):
                    if t < INTRO_DURATION + PAUSE_DURATION:
                        return (sep_pos, 0)
                    else:
                        scroll_time = t - (INTRO_DURATION + PAUSE_DURATION)
                        speed = (WIDTH + CARD_WIDTH) / (SCROLL_DURATION * 4)
                        x = sep_pos - (scroll_time * speed)
                        return (x, 0)
                return get_position

            separator_clip = separator.set_position(make_separator_position(i, separator_x))
            separator_clip = separator_clip.set_start(0)
            separator_clip = separator_clip.set_duration(INTRO_DURATION + PAUSE_DURATION + SCROLL_DURATION * 3.5)
            clips.append(separator_clip)

    # Phase 2: Scrolling animation for remaining cards
    for i in range(3, len(all_cards)):
        card = all_cards[i]
        start_time = INTRO_DURATION + PAUSE_DURATION + ((i - 3) * SCROLL_DURATION)
        duration = SCROLL_DURATION * 4

        def make_scroll_position_function():
            def get_position(t):
                start_x = WIDTH
                speed = (WIDTH + CARD_WIDTH) / (SCROLL_DURATION * 4)
                x = start_x - (t * speed)
                return (x, 0)
            return get_position

        moving_clip = card.set_position(make_scroll_position_function())
        moving_clip = moving_clip.set_start(start_time)
        moving_clip = moving_clip.set_duration(duration)
        clips.append(moving_clip)

        separator = create_separator(SEPARATOR_WIDTH, CARD_HEIGHT)

        def make_separator_scroll_position():
            def get_position(t):
                start_x = WIDTH - SEPARATOR_WIDTH
                speed = (WIDTH + CARD_WIDTH) / (SCROLL_DURATION * 4)
                x = start_x - (t * speed)
                return (x, 0)
            return get_position

        separator_clip = separator.set_position(make_separator_scroll_position())
        separator_clip = separator_clip.set_start(start_time)
        separator_clip = separator_clip.set_duration(duration)
        clips.append(separator_clip)

    # Total duration
    total_duration = INTRO_DURATION + PAUSE_DURATION + ((len(all_cards) - 3) * SCROLL_DURATION) + SCROLL_DURATION * 3

    # Create final video
    final_video = CompositeVideoClip(clips, size=(WIDTH, HEIGHT))
    final_video = final_video.set_duration(total_duration)

    # Export
    print(f"[video_engine] Export vers {output_file} ({WIDTH}x{HEIGHT} @ {FPS}fps)...")
    final_video.write_videofile(
        output_file,
        fps=FPS,
        codec='libx264',
        bitrate=bitrate,
        preset=preset,
        threads=threads,
        audio=False
    )
    print(f"[video_engine] Termine: {output_file}")
    return output_file
