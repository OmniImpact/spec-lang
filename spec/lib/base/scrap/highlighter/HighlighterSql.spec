#! Package base:scrap
#! Syntax highlighter for SQL queries and scripts (`.sql`), inheriting `Highlighter`.

Class of Highlighter is HighlighterSql{
	replace [String] is namespace: ['base', 'scrap', 'highlighter'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'fabric', Theme],
		['base', 'fabric', DrawContext],
		['base', 'scrap', 'highlighter', Highlighter]
	];

	String is keywords: ' ADD ALL ALTER AND ANY AS ASC AUTHORIZATION BACKUP BEGIN BETWEEN BREAK BROWSE BULK BY CASCADE CASE CHECK CHECKPOINT CLOSE CLUSTERED COALESCE COLLATE COLUMN COMMIT COMPUTE CONSTRAINT CONTAINS CONTINUE CONVERT CREATE CROSS CURRENT CURRENT_DATE CURRENT_TIME CURRENT_TIMESTAMP CURRENT_USER CURSOR DATABASE DBCC DEALLOCATE DECLARE DEFAULT DELETE DENY DESC DISK DISTINCT DISTRIBUTED DOUBLE DROP DUMP ELSE END ERRLVL ESCAPE EXCEPT EXEC EXECUTE EXISTS EXIT EXTERNAL FETCH FILE FILLFACTOR FOR FOREIGN FREETEXT FROM FULL FUNCTION GOTO GRANT GROUP HAVING HOLDLOCK IDENTITY IF IN INDEX INNER INSERT INTERSECT INTO IS JOIN KEY KILL LEFT LIKE LINENO LOAD MERGE NATIONAL NOCHECK NONCLUSTERED NOT NULL NULLIF OF OFF OFFSETS ON OPEN OPENDATASOURCE OPENQUERY OPENROWSET OPENXML OPTION OR ORDER OUTER OVER PERCENT PIVOT PLAN PRECISION PRIMARY PRINT PROC PROCEDURE PUBLIC RAISERROR READ READTEXT RECONFIGURE REFERENCES REPLICATION RESTORE RESTRICT RETURN REVERT REVOKE RIGHT ROLLBACK ROWCOUNT ROWGUIDCOL RULE SAVE SCHEMA SECURITYAUDIT SELECT SEMANTICKEYPHRASETABLE SEMANTICSIMILARITYDETAILSTABLE SEMANTICSIMILARITYTABLE SESSION_USER SET SETUSER SHUTDOWN SOME STATISTICS SYSTEM_USER TABLE TABLESAMPLE TEXTSIZE THEN TO TOP TRAN TRANSACTION TRIGGER TRUNCATE TRY_CONVERT TSEQUAL UNION UNIQUE UNPIVOT UPDATE UPDATETEXT USE USER VALUES VARYING VIEW WAITFOR WHEN WHERE WHILE WITH WITHIN GROUP WRITETEXT TRUE FALSE ';

	replace Function of String is languageId(){
		return 'sql';
	}

	replace Function of String is displayName(){
		return 'SQL';
	}

	replace Function of Highlighter is clone(){
		return HighlighterSql() as Highlighter;
	}

	replace Function of Boolean is matchesExtension(String is lowPath){
		return endsWith(s: lowPath, suffix: '.sql');
	}

	local Function of Boolean is isSqlPunct(Int is b){
		return b == 123 || b == 125 || b == 91 || b == 93 || b == 40 || b == 41 || b == 58 || b == 59 || b == 44 || b == 46;
	}

	replace Function is paintLine(DrawContext is ctx, Theme is theme, Int is x, Int is y, String is lineStr, Int is fpx){
		local Int is len: lineStr:length();
		local Int is i: 0;
		local Int is curX: x;
		while({ i < len }, {
			local Int is b: lineStr:byteAt(index: i) & 255;
			if({ b == 45 && i + 1 < len && (lineStr:byteAt(index: i + 1) & 255) == 45 }, {
				curX: drawSpan(ctx: ctx, curX: curX, y: y, seg: lineStr:substring(start: i, end: len), color: theme:synComment, fpx: fpx, bold: false, italic: true);
				return;
			});
			if({ b == 47 && i + 1 < len && (lineStr:byteAt(index: i + 1) & 255) == 42 }, {
				local Int is j: i + 2;
				local Boolean is closedCmt: false;
				while({ j < len && !closedCmt }, {
					if({ j + 1 < len && (lineStr:byteAt(index: j) & 255) == 42 && (lineStr:byteAt(index: j + 1) & 255) == 47 }, {
						j: j + 2;
						closedCmt: true;
					}, {
						j: j + 1;
					});
				});
				curX: drawSpan(ctx: ctx, curX: curX, y: y, seg: lineStr:substring(start: i, end: j), color: theme:synComment, fpx: fpx, bold: false, italic: true);
				i: j;
			}, {
			if({ b == 39 || b == 34 || b == 96 }, {
				local Int is q: b;
				local Int is j: i + 1;
				local Boolean is closedStr: false;
				while({ j < len && !closedStr }, {
					local Int is ch: lineStr:byteAt(index: j) & 255;
					if({ ch == 92 && j + 1 < len }, {
						j: j + 2;
					}, {
						if({ ch == q }, {
							j: j + 1;
							closedStr: true;
						}, {
							j: j + 1;
						});
					});
				});
				curX: drawSpan(ctx: ctx, curX: curX, y: y, seg: lineStr:substring(start: i, end: j), color: theme:synString, fpx: fpx, bold: false, italic: true);
				i: j;
			}, {
			if({ isDigit(b: b) }, {
				local Int is j: i + 1;
				while({ j < len && (isIdentChar(b: lineStr:byteAt(index: j) & 255) || (lineStr:byteAt(index: j) & 255) == 46) }, {
					j: j + 1;
				});
				curX: drawSpan(ctx: ctx, curX: curX, y: y, seg: lineStr:substring(start: i, end: j), color: theme:synNumber, fpx: fpx, bold: false, italic: false);
				i: j;
			}, {
			if({ isAlpha(b: b) }, {
				local Int is j: i + 1;
				while({ j < len && isIdentChar(b: lineStr:byteAt(index: j) & 255) }, {
					j: j + 1;
				});
				local String is word: lineStr:substring(start: i, end: j);
				if({ keywords:contains(needle: ' ' . word:toUpper() . ' ') }, {
					curX: drawSpan(ctx: ctx, curX: curX, y: y, seg: word, color: theme:synKeyword, fpx: fpx, bold: true, italic: false);
				}, {
					curX: drawSpan(ctx: ctx, curX: curX, y: y, seg: word, color: theme:textPrimary, fpx: fpx, bold: false, italic: false);
				});
				i: j;
			}, {
			if({ :isSqlPunct(b: b) }, {
				local Int is j: i + 1;
				local Boolean is keepPunct: true;
				while({ j < len && keepPunct }, {
					if({ :isSqlPunct(b: lineStr:byteAt(index: j) & 255) }, {
						j: j + 1;
					}, {
						keepPunct: false;
					});
				});
				curX: drawSpan(ctx: ctx, curX: curX, y: y, seg: lineStr:substring(start: i, end: j), color: theme:synPunct, fpx: fpx, bold: false, italic: false);
				i: j;
			}, {
				local Int is j: i + 1;
				local Boolean is stopPlain: false;
				while({ j < len && !stopPlain }, {
					local Int is nb: lineStr:byteAt(index: j) & 255;
					if({ nb == 45 || nb == 47 || nb == 39 || nb == 34 || nb == 96 || isDigit(b: nb) || isAlpha(b: nb) || :isSqlPunct(b: nb) }, {
						stopPlain: true;
					}, {
						j: j + 1;
					});
				});
				curX: drawSpan(ctx: ctx, curX: curX, y: y, seg: lineStr:substring(start: i, end: j), color: theme:textPrimary, fpx: fpx, bold: false, italic: false);
				i: j;
			}); }); }); }); });
		});
	}
}
