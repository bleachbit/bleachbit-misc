%define __strip %{_mingw32_strip}
%define __objdump %{_mingw32_objdump}
%define _use_internal_dependency_generator 0
%define __find_requires %{_mingw32_findrequires}
%define __find_provides %{_mingw32_findprovides}
%define __os_install_post %{_mingw32_debug_install_post} \
                          %{_mingw32_install_post}

Name:           mingw32-cairo
Version:        1.8.10
Release:        0
Summary:        MinGW Windows Cairo library

License:        LGPLv2 or MPLv1.1
URL:            http://cairographics.org
Source0:        http://cairographics.org/snapshots/cairo-%{version}.tar.gz
Group:          Development/Libraries
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildArch:      noarch
#!BuildIgnore: post-build-checks  

BuildRequires:  mingw32-filesystem >= 23
BuildRequires:  mingw32-cross-gcc
BuildRequires:  mingw32-cross-binutils
BuildRequires:  mingw32-libxml2-devel
BuildRequires:  mingw32-pixman-devel
BuildRequires:  mingw32-libpng-devel
BuildRequires:  pkgconfig

%description
MinGW Windows Cairo library.

%package devel
Summary:        MinGW Windows Cairo library (development files)
Group:          Development/Libraries
Requires:       mingw32-libpng-devel
Requires:       mingw32-pixman-devel

%description devel
MinGW Windows Cairo library (development files).


%{_mingw32_debug_package}

%prep
%setup -q -n cairo-%{version}

%build
echo "lt_cv_deplibs_check_method='pass_all'" >>%{_mingw32_cache}
%{_mingw32_configure} --disable-xlib --disable-xcb \
	--enable-win32 --enable-png \
	--disable-static --enable-shared \
	--enable-svg=no

grep "\-O2" Makefile
sed "s/-O2 -g/-Os/g" Makefile

%{_mingw32_make} %{?_smp_mflags} || %{_mingw32_make}


%install
rm -rf $RPM_BUILD_ROOT

make DESTDIR=$RPM_BUILD_ROOT install

rm -f $RPM_BUILD_ROOT%{_mingw32_libdir}/charset.alias

%clean
rm -rf $RPM_BUILD_ROOT


%files
%defattr(-,root,root)
%{_mingw32_bindir}/libcairo-2.dll


%files devel
%defattr(-,root,root)
%{_mingw32_includedir}/cairo/
%{_mingw32_libdir}/libcairo.dll.a
%{_mingw32_libdir}/pkgconfig/cairo-png.pc
%{_mingw32_libdir}/pkgconfig/cairo-win32-font.pc
%{_mingw32_libdir}/pkgconfig/cairo-win32.pc
%{_mingw32_libdir}/pkgconfig/cairo-pdf.pc
%{_mingw32_libdir}/pkgconfig/cairo-ps.pc
%{_mingw32_libdir}/pkgconfig/cairo.pc
%{_mingw32_datadir}/gtk-doc/html/cairo/


%changelog
* Wed Oct 29 2008 Richard W.M. Jones <rjones@redhat.com> - 1.8.0-2
- Fix mixed spaces/tabs in specfile.

* Fri Oct 24 2008 Richard W.M. Jones <rjones@redhat.com> - 1.8.0-1
- New upstream version 1.8.0.

* Wed Sep 24 2008 Richard W.M. Jones <rjones@redhat.com> - 1.7.4-4
- Rename mingw -> mingw32.

* Thu Sep 11 2008 Daniel P. Berrange <berrange@redhat.com> - 1.7.4-3
- Added dep on pkgconfig

* Wed Sep 10 2008 Richard W.M. Jones <rjones@redhat.com> - 1.7.4-2
- Remove static libraries.
- Fix source URL.

* Tue Sep  9 2008 Daniel P. Berrange <berrange@redhat.com> - 1.7.4-1
- Initial RPM release
