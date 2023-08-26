def excerpt_notification(text, length=35):
    if not isinstance(text, str):
        return f"{text}"

    # Split in words
    words = text.split()
    if len(words) == 1:  # Just one word
        return text[:length]
    cummulative_length = 0
    i = 0
    while i < len(words) and cummulative_length + len(words[i]) < length:
        cummulative_length = cummulative_length + len(words[i])
        i = i + 1
    if i == len(words):  # Text is short enough
        return text
    return " ".join(words[:i]) + " ..."
