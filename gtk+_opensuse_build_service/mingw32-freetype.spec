%define __strip %{_mingw32_strip}
%define __objdump %{_mingw32_objdump}
%define _use_internal_dependency_generator 0
%define __find_requires %{_mingw32_findrequires}
%define __find_provides %{_mingw32_findprovides}
%define __os_install_post %{_mingw32_debug_install_post} \
                          %{_mingw32_install_post}

Name:           mingw32-freetype
Version:        2.3.12
Release:        0
Summary:        MinGW Windows Freetype library

License:        FTL or GPLv2+
URL:            http://www.freetype.org
Source:         http://download.savannah.gnu.org/releases/freetype/freetype-%{version}.tar.bz2
Source1:         http://download.savannah.gnu.org/releases/freetype/freetype-doc-%{version}.tar.bz2
Group:          Development/Libraries
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildArch:      noarch
#!BuildIgnore: post-build-checks  

BuildRequires:  mingw32-filesystem >= 25
BuildRequires:  mingw32-cross-gcc
BuildRequires:  mingw32-cross-binutils
BuildRequires:  mingw32-zlib-devel

%description
MinGW Windows Freetype library.


%package devel
Summary:        MinGW Windows Freetype library
Group:          Development/Libraries
Requires:       mingw32-zlib-devel


%description devel
MinGW Windows Freetype library (development files).


%{_mingw32_debug_package}

%prep
%setup -q -n freetype-%{version} -b 1 -a 1
sed -i 's/^FONT_MODULES += /#&/g' modules.cfg
sed -i 's/^#FONT_MODULES += treetype/FONT_MODULES += truetype/g' modules.cfg
sed -i 's/^#FONT_MODULES += cff/FONT_MODULES += cff/g' modules.cfg

sed -i 's/^HINTING_MODULES += /#&/g' modules.cfg
sed -i 's/^AUX_MODULES += psaux/#&/g' modules.cfg
sed -i 's/^AUX_MODULES += lzw/#&/g' modules.cfg
sed -i 's/^AUX_MODULES += gzip/#&/g' modules.cfg

%build
echo "lt_cv_deplibs_check_method='pass_all'" >>builds/unix/%{_mingw32_cache} && chmod +w builds/unix/%{_mingw32_cache}
%{_mingw32_configure} --enable-shared --disable-static
make %{?_smp_mflags} || make


%install
rm -rf $RPM_BUILD_ROOT

make DESTDIR=$RPM_BUILD_ROOT install

%clean
rm -rf $RPM_BUILD_ROOT


%files
%defattr(-,root,root)
%{_mingw32_bindir}/libfreetype-6.dll


%files devel
%defattr(-,root,root)
%{_mingw32_bindir}/freetype-config
%{_mingw32_includedir}/freetype2
%{_mingw32_includedir}/ft2build.h
%{_mingw32_libdir}/libfreetype.dll.a
%{_mingw32_libdir}/pkgconfig/freetype2.pc
%{_mingw32_datadir}/aclocal/freetype2.m4


%changelog
* Wed Sep 24 2008 Richard W.M. Jones <rjones@redhat.com> - 2.3.7-5
- Rename mingw -> mingw32.

* Mon Sep 22 2008 Daniel P. Berrange <berrange@redhat.com> - 2.3.7-4
- Import patches from rawhide  & add docs

* Sun Sep 21 2008 Richard W.M. Jones <rjones@redhat.com> - 2.3.7-3
- Depends on filesystem >= 25.

* Wed Sep 10 2008 Richard W.M. Jones <rjones@redhat.com> - 2.3.7-2
- Fix source URL.
- Remove static libraries.

* Tue Sep  9 2008 Daniel P. Berrange <berrange@redhat.com> - 2.3.7-1
- Initial RPM release
