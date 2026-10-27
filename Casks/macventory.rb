cask "macventory" do
  version "1.1.0"
  sha256 "183dd721cdda80de376ce114b080729afac763e33fccb4354045cef576842e36"

  url "https://github.com/vadimtanel/MacVentory/releases/download/v#{version}/Macventory-#{version}-arm64.dmg"
  name "Macventory"
  desc "Software inventory and management"
  homepage "https://github.com/vadimtanel/MacVentory"

  depends_on arch: :arm64
  depends_on macos: :ventura

  app "Macventory.app"
end
