# Maintainer: Your Name <your@email.com>
pkgname=fmanager
pkgver=1.0
pkgrel=1
pkgdesc="Modern terminal file manager with curses interface"
arch=('any')
url="https://github.com/RedTeamSector7/Fmanager"
license=('GPL3')
depends=('python' 'ncurses')
source=("$pkgname-$pkgver.tar.gz")
sha256sums=('SKIP')

package() {
  cd "$srcdir/$pkgname-$pkgver"
  
  # Install binary
  install -Dm755 fmanager "$pkgdir/usr/bin/fmanager"
  
  # Install Python files
  install -dm755 "$pkgdir/opt/fmanager"
  cp -r src/* "$pkgdir/opt/fmanager/"
  
  # Install icons and desktop
  install -Dm644 icon.png "$pkgdir/usr/share/pixmaps/fmanager.png"
  install -Dm644 fmanager.desktop "$pkgdir/usr/share/applications/fmanager.desktop"
}