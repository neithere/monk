# Maintainer: Andrey Mikhaylenko <neithere at gmail dot com>
pkgname=python2-monk
pkgver=0.2.2
pkgrel=1
pkgdesc="A lightweight schema/query framework for MongoDB"
arch=(any)
url="http://bitbucket.org/neithere/monk/"
license=('LGPL3')
depends=('python2>=2.7' 'python2-pymongo')
makedepends=('python2-distribute')
provides=()
conflicts=()
replaces=()
backup=()
options=(!emptydirs)
install=
source=(http://pypi.python.org/packages/source/m/monk/monk-${pkgver}.tar.gz)
md5sums=('19c22c63d0966eef7efdff465f55badd')

build() {
   cd "${srcdir}/monk-${pkgver}"
   python2 setup.py install --root="${pkgdir}" --optimize=1 || exit 1
}