enum SendMode { original, compressed, textOnly }

SendMode selectSendMode({
  required double bytesPerSecond,
  required bool hasImage,
}) {
  if (!hasImage || bytesPerSecond < 32 * 1024) return SendMode.textOnly;
  if (bytesPerSecond < 256 * 1024) return SendMode.compressed;
  return SendMode.original;
}

