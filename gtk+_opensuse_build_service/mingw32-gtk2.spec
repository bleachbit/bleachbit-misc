%define __strip %{_mingw32_strip}
%define __objdump %{_mingw32_objdump}
%define _use_internal_dependency_generator 0
%define __find_requires %{_mingw32_findrequires}
%define __find_provides %{_mingw32_findprovides}
%define __os_install_post %{_mingw32_debug_install_post} \
                          %{_mingw32_install_post}

Name:           mingw32-gtk2
Version:        2.20.1
Release:        0
Summary:        MinGW Windows Gtk2 library

License:        LGPLv2+
Group:          Development/Libraries
URL:            http://www.gtk.org
Source0:        http://download.gnome.org/sources/gtk+/2.20/gtk+-%{version}.tar.bz2
Source100:      %{name}-rpmlintrc
Patch0:         gtk+-2.18.9-mingww64.patch
Patch2:         gtk+-2.16.6-libpng.patch
Patch3:         gtk+-2.20.1-xptheme.patch
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildArch:      noarch
#!BuildIgnore: post-build-checks  

BuildRequires:  mingw32-filesystem >= 23
BuildRequires:  mingw32-cross-gcc
BuildRequires:  mingw32-cross-binutils
BuildRequires:  mingw32-win_iconv-devel
BuildRequires:  mingw32-gettext-tools
BuildRequires:  mingw32-glib2-devel >= 2.19.7
BuildRequires:  mingw32-cairo-devel >= 1.6.0
#BuildRequires:  mingw32-libjasper-devel
BuildRequires:  mingw32-libpng-devel
#BuildRequires:  mingw32-libjpeg-devel
#BuildRequires:  mingw32-libtiff-devel
BuildRequires:  mingw32-pango-devel >= 1.20
BuildRequires:  mingw32-atk-devel >= 1.29.3
BuildRequires:  pkgconfig autoconf automake
BuildRequires:  libtool
#BuildRequires:  gtk-doc
# Native one for msgfmt
BuildRequires:  gettext-tools
# Native one for glib-genmarshal
BuildRequires:  glib2-devel
# Native one for gtk-update-icon-cache
BuildRequires:  gtk2
# Native one for gdk-pixbuf-csource
BuildRequires:  gtk2-devel
Requires:       %{name}-lang = %{version}


%description
MinGW Windows Gtk2 library.


%package devel
Summary:        MinGW Windows Gtk2 library
Group:          Development/Libraries
Requires:       mingw32-pango-devel >= 1.20 mingw32-glib2-devel >= 2.19.7
#Requires:       mingw32-libjasper-devel mingw32-libtiff-devel
Requires:       mingw32-win_iconv-devel mingw32-gettext-tools
Requires:       mingw32-cairo-devel >= 1.6.0 mingw32-libpng-devel
#Requires:       mingw32-libjpeg-devel 
Requires:       mingw32-atk-devel >= 1.13.0


%description devel
MinGW Windows Gtk2 library.


%{_mingw32_debug_package}

%lang_package

%prep
%setup -q -n gtk+-%{version}

%patch0 -p0 -b .mingww64
%patch2 -p1 -b .libpng
%patch3 -p1 -b .xptheme

%build
libtoolize --force --copy --install
autoreconf -f -i 
# Need to run the correct version of glib-mkenums.
export PATH="%{_mingw32_bindir}:$PATH"

echo "lt_cv_deplibs_check_method='pass_all'" >>%{_mingw32_cache}

#cups is pointless for win32 and gdiplus based loaders are utterly broken
%{_mingw32_configure} --disable-cups \
        --with-gdktarget=win32  \
        --with-included-loaders=yes --with-included-immodules=yes \
        --disable-dependency-tracking
        --disable-gdiplus \
        --disable-gtk-doc \
        --disable-gtk-doc-html \
        --disable-gtk-doc-pdf \
        --disable-papi \
        --disable-xinerama \
        --enable-debug=no \
        --enable-introspection=no \
        --without-libjasper \
        --without-libjpeg  \
        --without-libtiff \

rm -f gtk/gtk.def
make %{?_smp_mflags} || make


%install
rm -rf $RPM_BUILD_ROOT

make DESTDIR=$RPM_BUILD_ROOT install

rm -f $RPM_BUILD_ROOT%{_mingw32_libdir}/charset.alias

(echo 'gtk-theme-name = "MS-Windows"'
echo 'gtk-fallback-icon-theme = "Tango"') >$RPM_BUILD_ROOT%{_mingw32_sysconfdir}/gtk-2.0/gtkrc

%find_lang gtk20
%find_lang gtk20-properties gtk20.lang



%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)
%{_mingw32_datadir}/themes/*
%{_mingw32_bindir}/gdk-pixbuf-query-loaders.exe
%{_mingw32_bindir}/gtk-builder-convert
%{_mingw32_bindir}/gtk-query-immodules-2.0.exe
%{_mingw32_bindir}/gtk-update-icon-cache.exe
%{_mingw32_bindir}/gtk-update-icon-cache.exe.manifest
%{_mingw32_bindir}/libgailutil-18.dll
%{_mingw32_bindir}/libgdk-win32-2.0-0.dll
%{_mingw32_bindir}/libgdk_pixbuf-2.0-0.dll
%{_mingw32_bindir}/libgtk-win32-2.0-0.dll
%{_mingw32_libdir}/gtk-2.0/2.10.0/engines/*.dll
%{_mingw32_libdir}/gtk-2.0/modules/*.dll
%{_mingw32_sysconfdir}/gtk-2.0/

%files lang -f gtk20.lang
%defattr(-,root,root)

%files devel
%defattr(-,root,root)
#%{_mingw32_datadir}/gtk-doc/html/gail-libgail-util
#%{_mingw32_datadir}/gtk-doc/html/gdk-pixbuf
#%{_mingw32_datadir}/gtk-doc/html/gdk
#%{_mingw32_datadir}/gtk-doc/html/gtk
%{_mingw32_bindir}/gdk-pixbuf-csource.exe
%{_mingw32_bindir}/gtk-demo.exe
%{_mingw32_libdir}/libgailutil.dll.a
%{_mingw32_libdir}/libgdk-win32-2.0.dll.a
%{_mingw32_libdir}/libgdk_pixbuf-2.0.dll.a
%{_mingw32_libdir}/libgtk-win32-2.0.dll.a
%exclude %{_mingw32_libdir}/gdk_pixbuf-2.0.def
%exclude %{_mingw32_libdir}/gdk-win32-2.0.def
%exclude %{_mingw32_libdir}/gtk-win32-2.0.def
%exclude %{_mingw32_libdir}/gailutil.def
%{_mingw32_libdir}/pkgconfig/gail.pc
%{_mingw32_libdir}/pkgconfig/gdk-2.0.pc
%{_mingw32_libdir}/pkgconfig/gdk-win32-2.0.pc
%{_mingw32_libdir}/pkgconfig/gdk-pixbuf-2.0.pc
%{_mingw32_libdir}/pkgconfig/gtk+-2.0.pc
%{_mingw32_libdir}/pkgconfig/gtk+-win32-2.0.pc
%exclude %{_mingw32_libdir}/gtk-2.0/2.10.0/engines/*.dll.a
%exclude %{_mingw32_libdir}/gtk-2.0/modules/*.dll.a
%{_mingw32_includedir}/gtk-2.0/
%{_mingw32_libdir}/gtk-2.0/include/
%{_mingw32_includedir}/gail-1.0/
%{_mingw32_datadir}/aclocal/gtk-2.0.m4
%{_mingw32_datadir}/gtk-2.0/
%{_mingw32_mandir}


%changelog
* Mon Oct 27 2008 Richard W.M. Jones <rjones@redhat.com> - 2.14.4-3
- Remove preun script, no longer used.

* Fri Oct 24 2008 Richard W.M. Jones <rjones@redhat.com> - 2.14.4-1
- New upstream version 2.14.4.
- Require cairo >= 1.8.0 because of important fixes.
- Remove a couple of patches which are now upstream.

* Fri Oct 10 2008 Richard W.M. Jones <rjones@redhat.com> - 2.14.2-3
- Remove the requirement for Wine at build or install time.
- Conflicts with (native) cups-devel.

* Wed Sep 24 2008 Richard W.M. Jones <rjones@redhat.com> - 2.14.2-2
- Rename mingw -> mingw32.

* Mon Sep 22 2008 Daniel P. Berrange <berrange@redhat.com> - 2.14.2-1
- Update to 2.14.2 release

* Sun Sep 21 2008 Richard W.M. Jones <rjones@redhat.com> - 2.14.0-5
- Remove manpages duplicating those in Fedora native packages.

* Thu Sep 11 2008 Daniel P. Berrange <berrange@redhat.com> - 2.14.0-4
- Added dep on pkgconfig, gettext and glib2 (native)

* Thu Sep 11 2008 Richard W.M. Jones <rjones@redhat.com> - 2.14.0-3
- post/preun scripts to update the gdk-pixbuf.loaders list.

* Wed Sep 10 2008 Richard W.M. Jones <rjones@redhat.com> - 2.14.0-2
- Jasper DLLs now fixed.
- Fix source URL.
- Run the correct glib-mkenums.

* Tue Sep  9 2008 Daniel P. Berrange <berrange@redhat.com> - 2.14.0-1
- Initial RPM release
