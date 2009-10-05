%define tversion 2.5.14
%define apacheuser apache 
%define apachegroup apache 
%define webconf %{_sysconfdir}/httpd/conf/webapps.d/	
%define appdir %{_var}/www
%define oleversion 0.0.0

Summary: 	Web Based LDAP Administration Program 
Name:		gosa
Version: 	2.5.14
Release:	%mkrel 5
License: 	GPL
Source: 	ftp://oss.GONICUS.de/pub/gosa/beta/%{name}-%{tversion}.tar.bz2
Source1:	gosa.conf.mdv
Source2:	README.urpmi
# http://www.bettina-attack.de/jonny/view.php/projects/php_ole/
Source3:	php_ole-%{oleversion}.tar.bz2
URL: 		http://gosa.gonicus.de
Group: 		System/Configuration/Other
Requires:	apache-mod_php php-ldap php-imap php-mysql php-xml 
Requires:	php-gd php-cups php-iconv php-snmp
Requires:	fping imagemagick smbldap-tools php-mbstring
Buildarch: 	noarch
BuildRoot: 	%{_tmppath}/%{name}-%{version}-%{release}-buildroot
BuildRequires:  apache-base > 2.0.54 dos2unix

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
%setup -q -a 3 -n %{name}-%{tversion}
find . -depth -name CVS -type d | xargs rm -rf
cp %{SOURCE2} .

%build

%install
rm -rf %{buildroot}

mkdir -p %{buildroot}%{appdir}/%{name}

# (sb) seems broken - bad path to includes
sed -i 's|Excel/||g' include/php_writeexcel/class.excel.php
# (sb) copy the missing includes from SOURCE3 and rename docs
cp php_ole-%{oleversion}/*.php include/php_writeexcel
for i in README HOMEPAGE LICENSE; do \
  mv php_ole-%{oleversion}/$i $i.php_ole; \
done

DIRS="ihtml plugins html include locale"
for i in $DIRS; do \
  cp -ua $i %{buildroot}%{appdir}/%{name}/$i ; \
done

# (sb) make rpmlint happier
find doc -type f | xargs chmod -x

# (sb) error during setup if this isn't found
mkdir -p %{buildroot}%{appdir}/%{name}/contrib
cp -a contrib/gosa.conf %{buildroot}%{appdir}/%{name}/contrib

# (sb) used by smarty compile
mkdir -p %{buildroot}/var/spool/gosa

# Copy default config
mkdir -p %{buildroot}%{_sysconfdir}/%{name}
install -m 640 %{SOURCE1} %{buildroot}%{_sysconfdir}/%{name}/%{name}.conf
mkdir -p %{buildroot}%{webconf}

cat > %{buildroot}%{webconf}/%{name}.conf <<EOF
# Just to be sure
<Directory "%{appdir}/%{name}/html">
	Options None
	AllowOverride None
	Order allow,deny
	Allow from all
</Directory>
# Set alias to gosa
Alias /gosa %{appdir}/%{name}/html
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
dos2unix doc/guide/admin/es/manual_gosa_es_apache.tex

%post
%_post_webapp

%post schema
grep -q "^include %{_datadir}/openldap/schema/%{name}/%{name}-core.schema" %{_sysconfdir}/openldap/schema/local.schema || echo "include %{_datadir}/openldap/schema/%{name}/%{name}-core.schema" >> /etc/openldap/schema/local.schema
if [ -f /var/lock/subsys/ldap ]; then
    /etc/rc.d/init.d/ldap restart 1>&2;
fi

%postun
%_postun_webapp

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

%config(noreplace) %{webconf}/%{name}.conf
%attr(0750, %{apacheuser}, %{apachegroup}) %dir /var/spool/%{name}
%dir %{appdir}/%{name}
%{appdir}/%{name}/*
%dir %{_sysconfdir}/%{name}
%attr(0640, root, %{apachegroup}) %config(noreplace) %{_sysconfdir}/%{name}/%{name}.conf

%files schema
%doc COPYING AUTHORS README README.urpmi
%doc contrib/demo.ldif contrib/openldap/slapd.conf
%dir %{_datadir}/openldap/schema/%{name}
%{_datadir}/openldap/schema/%{name}/*


