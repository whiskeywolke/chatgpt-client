import PyInstaller.__main__

if __name__ == "__main__":
    PyInstaller.__main__.run([
        'chatgpt_client.py',
        '--onefile',
        # '--windowed'
        # "--noconsole",
        # "--noupx"
    ])
