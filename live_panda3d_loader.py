import sys
import os
from direct.showbase.ShowBase import ShowBase
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import importlib.util
import asyncio
import platform

# Path to the Panda3D game script
GAME_SCRIPT_PATH = "sample_panda3d.py"

class Panda3DLoader:
    def __init__(self):
        self.current_app = None
        self.observer = None

    def load_and_run(self):
        """Load and run the Panda3D game script."""
        try:
            # Clear previous module if it exists
            if 'game' in sys.modules:
                del sys.modules['game']

            # Load the module dynamically
            spec = importlib.util.spec_from_file_location("game", GAME_SCRIPT_PATH)
            if spec is None:
                print(f"Error: Could not load {GAME_SCRIPT_PATH}")
                return
            module = importlib.util.module_from_spec(spec)
            sys.modules['game'] = module
            spec.loader.exec_module(module)

            # Instantiate the game class (assumes the script defines Test class)
            if hasattr(module, 'Test'):
                # Clean up previous application if it exists
                if self.current_app:
                    self.current_app.destroy()
                    self.current_app = None

                # Create new instance of the game
                self.current_app = module.Test()
                self.current_app.run()
                print('in')
            else:
                print("Error: Test class not found in game.py")
        except Exception as e:
            print(f"Error loading {GAME_SCRIPT_PATH}: {e}")

    def start_watching(self):
        """Start monitoring the game script for changes."""
        class FileChangeHandler(FileSystemEventHandler):
            def __init__(self, loader):
                self.loader = loader

            def on_modified(self, event):
                if not event.is_directory and event.src_path.endswith(GAME_SCRIPT_PATH):
                    print(f"Detected change in {GAME_SCRIPT_PATH}. Reloading...")
                    self.loader.load_and_run()

        # Set up the file system observer
        self.observer = Observer()
        event_handler = FileChangeHandler(self)
        self.observer.schedule(event_handler, path=os.path.dirname(GAME_SCRIPT_PATH) or '.', recursive=False)
        self.observer.start()

    async def main(self):
        """Main async function to run the loader."""
        # Initial load and run
        self.load_and_run()

        # Keep the script running to monitor file changes
        while True:
            await asyncio.sleep(1)

    def stop(self):
        """Stop the observer and clean up."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
        if self.current_app:
            self.current_app.destroy()

if platform.system() == "Emscripten":
    loader = Panda3DLoader()
    loader.start_watching()
    asyncio.ensure_future(loader.main())
else:
    if __name__ == "__main__":
        loader = Panda3DLoader()
        loader.start_watching()
        try:
            asyncio.run(loader.main())
        except KeyboardInterrupt:
            loader.stop()