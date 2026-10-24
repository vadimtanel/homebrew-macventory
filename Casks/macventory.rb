cask "macventory" do
  version "1.0.0"
  sha256 "b7a2a64c5a5a17667e933195d383f0782d6b4ae27e8b27d39df76b65382bbcbf"

  url "https://github.com/vadimtanel/MacVentory/releases/download/v#{version}/Macventory-#{version}-arm64.dmg"
  name "Macventory"
  desc "Software inventory and management"
  homepage "https://github.com/vadimtanel/MacVentory"

  depends_on arch: :arm64
  depends_on macos: :ventura

  app "Macventory.app"
end
