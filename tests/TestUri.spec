#! specunit: suite
#! Comprehensive unit test suite for cross-platform URI and path abstraction (base:sys:Uri).

Class of SpecUnitTest is TestUri{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'sys', as Uri()],
		['base', 'sys', Uri]
	];

	Function is testPosixPaths(){
		local Uri is u: Uri:fromFilePath(filePath: '/home/user/spec/test.spec');
		Assert:areEqualString('file', u:scheme);
		Assert:areEqualString('/home/user/spec/test.spec', u:path);
		Assert:areEqualString('/home/user/spec/test.spec', u:toFilePath());
		Assert:areEqualString('file:///home/user/spec/test.spec', u:toString());
		Assert:isTrue(u:isAbsolute());
		Assert:areEqualString('/home/user/spec', u:dirPath());
		Assert:areEqualString('test.spec', u:baseName());
		Assert:areEqualString('.spec', u:extName());
	}

	Function is testWindowsDriveLetters(){
		local Uri is u: Uri:fromFilePath(filePath: 'C:\\Users\\runneradmin\\Spec\\test.spec');
		Assert:areEqualString('file', u:scheme);
		Assert:areEqualString('/C:/Users/runneradmin/Spec/test.spec', u:path);
		Assert:areEqualString('C:/Users/runneradmin/Spec/test.spec', u:toFilePath());
		Assert:areEqualString('file:///C:/Users/runneradmin/Spec/test.spec', u:toString());
		Assert:isTrue(u:isAbsolute());
		Assert:areEqualString('/C:/Users/runneradmin/Spec', u:dirPath());
		Assert:areEqualString('test.spec', u:baseName());
		Assert:areEqualString('.spec', u:extName());

		local Uri is uSlash: Uri:fromFilePath(filePath: 'd:/projects/app/main.spec');
		Assert:areEqualString('file', uSlash:scheme);
		Assert:areEqualString('/d:/projects/app/main.spec', uSlash:path);
		Assert:areEqualString('d:/projects/app/main.spec', uSlash:toFilePath());
	}

	Function is testRelativePaths(){
		local Uri is u: Uri:fromFilePath(filePath: 'utilities\\specbuild\\SpecBuild.spec');
		Assert:areEqualString('', u:scheme);
		Assert:areEqualString('utilities/specbuild/SpecBuild.spec', u:path);
		Assert:areEqualString('utilities/specbuild/SpecBuild.spec', u:toFilePath());
		Assert:areEqualString('utilities/specbuild/SpecBuild.spec', u:toString());
		Assert:isFalse(u:isAbsolute());
		Assert:areEqualString('utilities/specbuild', u:dirPath());
		Assert:areEqualString('SpecBuild.spec', u:baseName());
		Assert:areEqualString('.spec', u:extName());
	}

	Function is testNormalization(){
		# Dot and dot-dot resolution
		local String is p1: Uri:cleanPath(rawPath: 'a/b/../c');
		Assert:areEqualString('a/c', p1);

		local String is p2: Uri:cleanPath(rawPath: 'a/./b/./c');
		Assert:areEqualString('a/b/c', p2);

		local String is p3: Uri:cleanPath(rawPath: 'utilities/specunit/../../bin/specunit');
		Assert:areEqualString('bin/specunit', p3);

		local String is p4: Uri:cleanPath(rawPath: '/var/log/../../etc/passwd');
		Assert:areEqualString('/etc/passwd', p4);

		local String is p5: Uri:cleanPath(rawPath: 'C:\\foo\\bar\\..\\baz');
		Assert:areEqualString('C:/foo/baz', p5);

		local String is p6: Uri:cleanPath(rawPath: 'a//b///c');
		Assert:areEqualString('a/b/c', p6);
	}

	Function is testResolution(){
		local Uri is base: Uri:fromFilePath(filePath: 'utilities/specbuild/specbuild.json');
		local Uri is resolved: base:resolve(relativePath: 'SpecBuild.spec');
		Assert:areEqualString('utilities/specbuild/SpecBuild.spec', resolved:toFilePath());

		local Uri is resolvedUp: base:resolve(relativePath: '../../bin/specbuild');
		Assert:areEqualString('bin/specbuild', resolvedUp:toFilePath());

		local Uri is resolvedAbs: base:resolve(relativePath: '/opt/spec/bin');
		Assert:areEqualString('/opt/spec/bin', resolvedAbs:toFilePath());
		Assert:isTrue(resolvedAbs:isAbsolute());
	}

	Function is testParseFileUri(){
		local Uri is uPosix: Uri:parse(text: 'file:///usr/local/bin/spec');
		Assert:areEqualString('file', uPosix:scheme);
		Assert:areEqualString('/usr/local/bin/spec', uPosix:path);
		Assert:areEqualString('/usr/local/bin/spec', uPosix:toFilePath());

		local Uri is uWin: Uri:parse(text: 'file:///C:/Users/Admin/spec.exe');
		Assert:areEqualString('file', uWin:scheme);
		Assert:areEqualString('/C:/Users/Admin/spec.exe', uWin:path);
		Assert:areEqualString('C:/Users/Admin/spec.exe', uWin:toFilePath());
		Assert:areEqualString('.exe', uWin:extName());
		Assert:areEqualString('spec.exe', uWin:baseName());
	}

	Function is testUncPaths(){
		local Uri is u: Uri:fromFilePath(filePath: '\\\\server\\share\\folder\\file.txt');
		Assert:areEqualString('file', u:scheme);
		Assert:areEqualString('server', u:authority);
		Assert:areEqualString('/share/folder/file.txt', u:path);
		Assert:areEqualString('//server/share/folder/file.txt', u:toFilePath());
		Assert:areEqualString('file://server/share/folder/file.txt', u:toString());
	}

	Function is testSystemPaths(){
		local String is td: Uri:systemTempDir();
		Assert:isTrue(td:length() > 0);
		Assert:isFalse(td:endsWith(suffix: '/'));

		local String is hd: Uri:homeDir();
		if({ hd:length() > 0 }, {
			Assert:isFalse(hd:endsWith(suffix: '/'));
		});

		local String is cd: Uri:cacheDir();
		Assert:isTrue(cd:length() > 0);
		Assert:isFalse(cd:endsWith(suffix: '/'));

		local String is rcd: Uri:runtimeCacheDir();
		Assert:areEqualString(cd . '/runtime', rcd);

		local String is j: Uri:join(parts: ['a', 'b/c', '../d', 'e']);
		Assert:areEqualString('a/b/d/e', j);

		local String is tf: Uri:tempFile(prefix: 'test_', suffix: '.tmp');
		Assert:isTrue(tf:startsWith(prefix: td));
		Assert:isTrue(tf:endsWith(suffix: '.tmp'));
	}
}
