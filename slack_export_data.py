import os
import json
from pathlib import Path
import shutil
import tempfile


class SlackExportData:
    def __init__(self, dir_path: str) -> None:
        export_data_path = Path(dir_path)
        if not export_data_path.is_dir:
            raise ValueError
        self.path = Path(dir_path)
        self.channels = SlackJSONDataChannel(self.path/'channels.json')
        self.integration_logs = SlackJSONDataIntegrationLogs(
            self.path/'integration_logs.json')
        self.users = SlackJSONDataUsers(self.path/'users.json')
        self.channelDirectories = []

        for channel in self.channels:
            self.channelDirectories.append(
                SlackChannelDirectory(self.path/channel['name']))

    def getMessagesByClientMsgId(self, id):
        for channel in self.channelDirectories:
            for message_file in channel.messages:
                for message in message_file.json:
                    if ('client_msg_id' in message):
                        if message['client_msg_id'] == id:
                            return message

    def getHostedFileInfoByFileID(self, id):
        for channel in self.channelDirectories:
            for message_file in channel.messages:
                for message in message_file.json:
                    if ('files' in message):
                        for file in message['files']:
                            if ('id' in file and 'mode' in file):
                                if (file['id'] == id and file['mode'] == 'hosted'):
                                    return file
        return None

    def printFileStructure(self):
        print(' *** File structure ***')
        self.channels.printFileStructure()
        self.integration_logs.printFileStructure()
        self.users.printFileStructure()
        for channelDirectory in self.channelDirectories:
            print('[{}]'.format(channelDirectory.channelDirName))
            for message in channelDirectory.messages:
                print(' - {}'.format(message.filename))

    def getArchiveJSONData(self, path):
        with tempfile.TemporaryDirectory() as tempDir:
            pathTempDir = Path(tempDir)
            self.channels.outputJSONFile(pathTempDir)
            self.integration_logs.outputJSONFile(pathTempDir)
            self.users.outputJSONFile(pathTempDir)
            for channel in self.channelDirectories:
                chDirPath = pathTempDir/channel.channelDirName
                os.mkdir(chDirPath)
                for message in channel.messages:
                    message.outputJSONFile(chDirPath)
            shutil.make_archive(path, 'zip', tempDir)

    def getNumberOfMessage(self):
        message_num = 0
        for channelDirectory in self.channelDirectories:
            ch_message_num = 0
            for message in channelDirectory.messages:
                ch_message_num += len(message.json)
            print('[{}] {}'.format(
                channelDirectory.channelDirName, ch_message_num))
            message_num += ch_message_num
        print('---\nTotal : {}'.format(message_num))
        return message_num


class SlackJSONData:
    def __init__(self, path: str) -> None:
        self.filepath = Path(path).resolve()
        self.filename = self.filepath.name
        with open(self.filepath) as f:
            self.json = json.load(f)

    def __iter__(self):
        return iter(self.json)

    def printFileStructure(self):
        print(self.filename)

    def outputJSONFile(self, path):
        outputPath = Path(path)
        with open(outputPath/self.filename, 'w') as f:
            json.dump(self.json, f, indent=4, ensure_ascii=False)


class SlackJSONDataChannel(SlackJSONData):
    def __init__(self, path: str) -> None:
        super().__init__(path)


class SlackJSONDataIntegrationLogs(SlackJSONData):
    def __init__(self, path: str) -> None:
        super().__init__(path)


class SlackJSONDataUsers(SlackJSONData):
    def __init__(self, path: str) -> None:
        super().__init__(path)

    def getUserByID(self, id):
        for user in self.json:
            if (user['id'] == id):
                return user
        return None


class SlackChannelDirectory:
    def __init__(self, path: str) -> None:
        self.path = Path(path)
        self.channelDirName = self.path.parts[-1]
        self.messages = []
        json_files = self.path.glob('*.json')
        for file in json_files:
            self.messages.append(SlackJSONMessage(file))


class SlackJSONMessage(SlackJSONData):
    def __init__(self, path: str) -> None:
        super().__init__(path)
