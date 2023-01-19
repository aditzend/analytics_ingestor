import time
from watchdog.observers.polling import PollingObserver as Polling
from watchdog.events import FileSystemEventHandler
from pydub import AudioSegment
import sox
import os
import shutil


class Watcher:

    def __init__(self, directory=".", handler=FileSystemEventHandler()):
        self.observer = Polling(timeout=20)
        self.handler = handler
        self.directory = directory

    def run(self):
        self.observer.schedule(
            self.handler, self.directory, recursive=True)
        self.observer.start()
        print("\nWatcher Running in {}/\n".format(self.directory))
        try:
            while True:
                time.sleep(1)
        except:
            self.observer.stop()
        self.observer.join()
        print("\nWatcher Terminated\n")


class MyHandler(FileSystemEventHandler):

    # def on_any_event(self, event):
    #     print(event)  # Your code here

    def on_created(self, event):
        path = event.src_path

        # Print only if the file ends with .mp3
        # if not os.path.exists('/Users/alexander/Downloads/calls/queued'):
        #     os.makedirs('/Users/alexander/Downloads/calls/queued')
        if not os.path.exists('/Users/alexander/Downloads/calls/processed'):
            os.makedirs('/Users/alexander/Downloads/calls/processed')
        # shutil.move(event.src_path,
        #             '/Users/alexander/Downloads/calls/queued')
        # path = '/Users/alexander/Downloads/calls/queued' + event.src_path
        if event.src_path.endswith('.mp3'):
            # stereo = AudioSegment.from_file(event.src_path, format='mp3')
            # monos = stereo.split_to_mono()
            # mono_left = monos[0].export(
            #     event.src_path + '-left.mp3', format='mp3')
            sample_rate = sox.file_info.sample_rate(path)
            n_samples = sox.file_info.num_samples(path)
            duration = sox.file_info.duration(path)
            is_silent = sox.file_info.silent(path)
            channels = sox.file_info.channels(path)
            print('Sample rate: {}'.format(sample_rate))
            print('Number of samples: {}'.format(n_samples))
            print('Duration: {}'.format(duration))
            print('Is silent: {}'.format(is_silent))
            print('Channels: {}'.format(channels))
            shutil.move(path,
                        '/Users/alexander/Downloads/calls/processed')
            print('Moved: {}'.format(path))
            # mono_right = monos[1].export(
            #     event.src_path + '-right.mp3', format='mp3')
        # if processed directory is not created on local path create it

        # move file to processed directory


if __name__ == "__main__":
    w = Watcher("/Users/alexander/Downloads/calls", MyHandler())
    # w.run()
    # create an inifinite interval tthat watches over the directory
    # and lists the files that are still there
    while True:
        # print all mp3 files in the directory

        print(os.listdir("/Users/alexander/Downloads/calls"))
        time.sleep(20)
