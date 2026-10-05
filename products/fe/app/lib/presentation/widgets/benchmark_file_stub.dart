class Platform {
  static const pathSeparator = '/';
}

class File {
  File(String path);

  Future<bool> exists() async => false;
  Future<void> delete() async =>
      throw UnsupportedError('Local files unavailable');
  Future<RandomAccessFile> open() async =>
      throw UnsupportedError('Local files unavailable');
  Future<File> rename(String path) async =>
      throw UnsupportedError('Local files unavailable');
}

class RandomAccessFile {
  Future<int> length() async =>
      throw UnsupportedError('Local files unavailable');
  Future<List<int>> read(int count) async =>
      throw UnsupportedError('Local files unavailable');
  Future<void> setPosition(int position) async =>
      throw UnsupportedError('Local files unavailable');
  Future<void> close() async {}
}
