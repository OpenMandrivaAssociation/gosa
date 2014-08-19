%define apacheuser apache 
%define apachegroup apache 
%define oleversion 0.0.0

Summary: 	Web Based LDAP Administration Program 
Name:		gosa
Version: 	2.5.14
Release:	9.1
License: 	GPL
Group: 		System/Configuration/Other
URL: 		http://gosa.gonicus.de
Source: 	ftp://oss.GONICUS.de/pub/gosa/beta/%{name}-%{version}.tar.bz2
Source1:	gosa.conf.mdv
Source2:	README.urpmi
# http://www.bettina-attack.de/jonny/view.php/projects/php_ole/
Source3:	php_ole-%{oleversion}.tar.bz2
Requires:	apache-mod_php
Requires:	php-ldap
Requires:	php-imap
Requires:	php-mbstring
Requires:	php-mysql
Requires:	php-xml 
Requires:	php-gd
Requires:	php-snmp
Requires:	php-iconv
Requires:	php-cups
Requires:	fping
Requires:	imagemagick
Requires:	smbldap-tools
%if %mdkversion < 201010
Requires(post):   rpm-helper
Requires(postun):   rpm-helper
%endif
Buildarch: 	noarch
BuildRoot: 	%{_tmppath}/%{name}-%{version}

%description
GOsa is a combination of system-administrator and end-user web
interface, designed to handle LDAP based setups.
Provided is access to posix, shadow, samba, proxy, fax, and kerberos
accounts. It is able to manage the postfix/cyrus server combination
and can write user adapted sieve scripts.

Access GOsa at http://localhost/gosa/

%package schema
Group: 		System/Configuration/Other
Summary:        Schema Definitions for the GOSA package
Requires:	openldap-servers openldap-clients

%description schema
Contains the Schema definition files for the GOSA admin package.

%prep
%setup -q -a 3
find . -depth -name CVS -type d | xargs rm -rf
cp %{SOURCE2} .

%build

%install
rm -rf %{buildroot}

mkdir -p %{buildroot}%{_datadir}/%{name}

# (sb) seems broken - bad path to includes
sed -i 's|Excel/||g' include/php_writeexcel/class.excel.php
# (sb) copy the missing includes from SOURCE3 and rename docs
cp php_ole-%{oleversion}/*.php include/php_writeexcel
for i in README HOMEPAGE LICENSE; do \
  mv php_ole-%{oleversion}/$i $i.php_ole; \
done

DIRS="ihtml plugins html include locale"
for i in $DIRS; do \
  cp -ua $i %{buildroot}%{_datadir}/%{name}/$i ; \
done

# (sb) make rpmlint happier
find doc -type f | xargs chmod -x

# (sb) error during setup if this isn't found
mkdir -p %{buildroot}%{_datadir}/%{name}/contrib
cp -a contrib/gosa.conf %{buildroot}%{_datadir}/%{name}/contrib

# (sb) used by smarty compile
mkdir -p %{buildroot}/var/spool/gosa

# Copy default config
mkdir -p %{buildroot}%{_sysconfdir}/%{name}
install -m 640 %{SOURCE1} %{buildroot}%{_sysconfdir}/%{name}/%{name}.conf
mkdir -p %{buildroot}%{_webappconfdir}

cat > %{buildroot}%{_webappconfdir}/%{name}.conf <<EOF
Alias /gosa %{_datadir}/%{name}/html

<Directory %{_datadir}/%{name}/html>
    Order deny,allow
    Deny from all
    Allow from 127.0.0.1
    ErrorDocument 403 "Access denied per %{_webappconfdir}/%{name}.conf"
</Directory>
EOF

mkdir -p %{buildroot}%{_datadir}/openldap/schema/%{name}
mv contrib/openldap/*.schema %{buildroot}%{_datadir}/openldap/schema/%{name}

cat > %{buildroot}%{_datadir}/openldap/schema/%{name}/%{name}-core.schema <<EOF
include %{_datadir}/openldap/schema/%{name}/goconfig.schema
include %{_datadir}/openldap/schema/%{name}/gofax.schema
include %{_datadir}/openldap/schema/%{name}/gofon.schema
include %{_datadir}/openldap/schema/%{name}/gosystem.schema
include %{_datadir}/openldap/schema/%{name}/goserver.schema
include %{_datadir}/openldap/schema/%{name}/goto.schema
include %{_datadir}/openldap/schema/%{name}/gosa+samba3.schema
include %{_datadir}/openldap/schema/%{name}/pureftpd.schema
EOF

cat > %{buildroot}%{_datadir}/openldap/schema/%{name}/example.ldif <<EOF
# Organization for Example Corporation
# load this ldif before gosa.ldif (for an empty opendap db)
dn: dc=example,dc=com
objectClass: dcObject
objectClass: organization
dc: example
o: Example Corporation
description: The Example Corporation

# Organizational Role for Directory Manager
dn: cn=Manager,dc=example,dc=com
objectClass: organizationalRole
cn: Manager
description: Directory Manager

# groups
dn: ou=Group,dc=example,dc=com
objectClass: organizationalUnit
ou: Group
description: Groups

# users
#dn: ou=People,dc=example,dc=com
#objectClass: organizationalUnit
#ou: People
#description: Users
EOF

cat > %{buildroot}%{_datadir}/openldap/schema/%{name}/%{name}.ldif <<EOF
# Sample GOsa ldif
# username "admin", password "tester", group "administrators"

# groups - may not be needed, in an fresh install I found I needed it
dn: ou=groups,dc=example,dc=com
objectClass: organizationalUnit
ou: groups
description: Groups

# users - may not be needed, in a fresh install I found I needed it
dn: ou=people,dc=example,dc=com
objectClass: organizationalUnit
ou: people
description: Users

dn: cn=admin,ou=people,dc=example,dc=com
objectClass: person
objectClass: organizationalPerson
objectClass: inetOrgPerson
objectClass: gosaAccount
uid: admin
cn: admin
givenName: admin
sn: GOsa main administrator
sambaLMPassword: 10974C6EFC0AEE1917306D272A9441BB
sambaNTPassword: 38F3951141D0F71A039CFA9D1EC06378
userPassword:: dGVzdGVy

dn: cn=administrators,ou=groups,dc=example,dc=com
objectClass: gosaObject
objectClass: posixGroup
gosaSubtreeACL: :all
cn: administrators
gidNumber: 999
memberUid: admin
EOF

# (sb) rpmlint
chmod +x contrib/scripts/*.pl


%post schema
grep -q "^include %{_datadir}/openldap/schema/%{name}/%{name}-core.schema" %{_sysconfdir}/openldap/schema/local.schema || echo "include %{_datadir}/openldap/schema/%{name}/%{name}-core.schema" >> /etc/openldap/schema/local.schema
if [ -f /var/lock/subsys/ldap ]; then
    /etc/rc.d/init.d/ldap restart 1>&2;
fi


%postun schema
sed -i "s|^include %{_datadir}/openldap/schema/%{name}/%{name}-core.schema||" %{_sysconfdir}/openldap/schema/local.schema
if [ "$1" = "0" ]; then
    if [ -f /var/lock/subsys/ldap ]; then
        /etc/rc.d/init.d/ldap restart 1>&2
    fi
fi

%clean
rm -rf %{buildroot}

%files
%defattr(-,root,root)
%doc AUTHORS README README.urpmi
%doc Changelog COPYING INSTALL FAQ doc/* 
#%doc contrib/altlinux contrib/fix_config.sh 
#%doc contrib/mysql contrib/opensides contrib/patches 
%doc contrib/scripts contrib/vacation_example.txt
%doc *.php_ole

%config(noreplace) %{_webappconfdir}/%{name}.conf
%attr(0750, %{apacheuser}, %{apachegroup}) %dir /var/spool/%{name}
%{_datadir}/%{name}
%dir %{_sysconfdir}/%{name}
%attr(0640, root, %{apachegroup}) %config(noreplace) %{_sysconfdir}/%{name}/%{name}.conf

%files schema
%doc COPYING AUTHORS README README.urpmi
%doc contrib/demo.ldif contrib/openldap/slapd.conf
%dir %{_datadir}/openldap/schema/%{name}
%{_datadir}/openldap/schema/%{name}/*


%changelog
* Sun Dec 05 2010 Oden Eriksson <oeriksson@mandriva.com> 2.5.14-7mdv2011.0
+ Revision: 610963
- rebuild

* Tue Feb 23 2010 Guillaume Rousse <guillomovitch@mandriva.org> 2.5.14-6mdv2010.1
+ Revision: 510425
- rely on filetrigger for reloading apache configuration begining with 2010.1,
  rpm-helper macros otherwise
- install under %%{_datadir}, rather than %%{_localstatedir}

* Mon Oct 05 2009 Guillaume Rousse <guillomovitch@mandriva.org> 2.5.14-5mdv2010.0
+ Revision: 454237
- small spec cleanup
- don't duplicate spec-helper job
- fix dependencies, php-mhash doesn't exist anymore

* Fri Sep 04 2009 Thierry Vignaud <tv@mandriva.org> 2.5.14-4mdv2010.0
+ Revision: 429289
- rebuild

  + Oden Eriksson <oeriksson@mandriva.com>
    - lowercase ImageMagick

* Thu Jul 24 2008 Thierry Vignaud <tv@mandriva.org> 2.5.14-3mdv2009.0
+ Revision: 246521
- rebuild

* Wed Dec 26 2007 Emmanuel Andry <eandry@mandriva.org> 2.5.14-1mdv2008.1
+ Revision: 137818
- New version

  + Olivier Blin <oblin@mandriva.com>
    - restore BuildRoot

  + Thierry Vignaud <tv@mandriva.org>
    - kill re-definition of %%buildroot on Pixel's request

* Sun Sep 30 2007 Emmanuel Andry <eandry@mandriva.org> 2.5.8-2mdv2008.0
+ Revision: 93932
- drop requires php-kadm5 (bug #33143)


* Sat Feb 17 2007 Emmanuel Andry <eandry@mandriva.org> 2.5.8-1mdv2007.0
+ Revision: 122155
- New version 2.5.8
- Import gosa

* Tue Sep 12 2006 Emmanuel Andry <eandry@mandriva.org> 2.5.2-2mdv2007.0
- fix bug #22556

* Mon Aug 14 2006 Emmanuel Andry <eandry@mandriva.org> 2.5.2-1mdv2007.0
- 2.5.2
- switch to php5

* Mon Jun 19 2006 Emmanuel Andry <eandry@mandriva.org> 2.5.1-1mdv2007.0
- 2.5.1
- %%mkrel

* Wed Mar 29 2006 Stew Benedict <sbenedict@mandriva.com> 2.4-1mdk
- 2.4
- drop P0
- drop help workaround in %%install (online help is still in TODO)
- fix bad paths in include/php_writeexcel/class.excel.php
- add SOURCE3 to get missing includes for the embedded WriteExcel
- update requires, README.urpmi

* Sat Oct 01 2005 Stew Benedict <sbenedict@mandriva.com> 2.4-0.beta2.2mdk
- split into gosa, gosa-schema
- fix %%postun, clarify README.urpmi

* Fri Sep 30 2005 Stew Benedict <sbenedict@mandriva.com> 2.4-0.beta2.1mdk
- First Mandriva release (2.3 is too buggy according to mail list)

* Mon Feb 21 2005 Lars Scheiter <lars.scheiter@GONICUS.de> 2.3
- Update version to 2.3 (upstream)

