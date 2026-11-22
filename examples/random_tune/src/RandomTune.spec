#! Random Pentatonic Sine-Wave Tune
#! Exercises high-resolution timing (base:sys:Time, base:sys:DateTime),
#! trigonometry & RNG (base:math:Math), raw PCM audio (base:audio:Audio),
#! and SpecUnit-style Cleo terminal output.

## Generates and plays a 12-note random pentatonic melody with high-resolution interval timing.
Class is RandomTune{

	replace Array of Array of String is using: [
		['base', 'cleo', Cleo],
		['base', 'cleo', CleoSection],
		['base', 'cleo', CleoColor],
		['base', 'cleo', as CleoColor()],
		['base', 'cleo', CleoWidth],
		['base', 'cleo', as CleoWidth()],
		['base', 'cleo', BorderStyle],
		['base', 'cleo', TitlePlacement],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Time()],
		['base', 'sys', as DateTime()],
		['base', 'math', as Math()],
		['base', 'audio', as Audio()],
		['base', 'core', SpecError],
		['base', 'sys', AudioError],
		['base', 'struct', Array],
		['base', 'struct', List],
		[Synth]
	];

	## Entry point; opens the audio device (falling back to silent timing if unavailable) and plays 12 notes.
	replace Function is init(){
		local DateTime is startedAt: DateTime:now();
		local Cleo is ui: Cleo(
			title: ' random_tune ',
			titleColor: CleoColor:ansi(code: 255),
			titleBgColor: CleoColor:ansi(code: 236),
			width: CleoWidth:percent(pct: 100),
			outerBorder: BorderStyle:ROUNDED,
			dividerBorder: BorderStyle:THIN,
			borderColor: CleoColor:ansi(code: 240),
			dividerColor: CleoColor:ansi(code: 237)
		);
		local CleoSection is infoSec: ui:addSection(
			title: ' Session ',
			titleColor: CleoColor:ansi(code: 254),
			titleBgColor: CleoColor:ansi(code: 237),
			titlePlacement: TitlePlacement:INLINE_BORDER,
			fgColor: CleoColor:ansi(code: 250)
		);
		local CleoSection is notesSec: ui:addSection(
			title: ' Pentatonic Sequence ',
			titleColor: CleoColor:ansi(code: 254),
			titleBgColor: CleoColor:ansi(code: 237),
			titlePlacement: TitlePlacement:INLINE_BORDER,
			fgColor: CleoColor:ansi(code: 250)
		);
		local CleoSection is summarySec: ui:addSection(
			title: ' Timing Summary ',
			titleColor: CleoColor:ansi(code: 254),
			titleBgColor: CleoColor:ansi(code: 237),
			titlePlacement: TitlePlacement:INLINE_BORDER,
			fgColor: CleoColor:ansi(code: 250)
		);

		local Array of Int is scaleMidi: [60, 62, 64, 67, 69, 72, 74, 76];
		local Array of Str is scaleNames: ['C4', 'D4', 'E4', 'G4', 'A4', 'C5', 'D5', 'E5'];
		local Int is sampleRate: 44100;
		local Int is noteCount: 12;
		local Int is stepMs: 180;
		local Int is noteMs: 150;
		local Synth is synth: Synth();

		local String is audioErr: '';
		local Audio is audio: Audio:open(
			sampleRate: sampleRate,
			channels: 2,
			format: 1,
			onError: local Function(SpecError of AudioError is error){
				audioErr: error:description;
			}
		);
		local String is audioStatus: if({ audio:isOpen() }, { '44100 Hz stereo PCM' }, { "silent mode ({{audioErr}})" });
		infoSec:addLine(text: "Started: {{startedAt:formatIso()}}", color: CleoColor:ansi(code: 252), rightText: audioStatus);

		local Int is idx: 0;
		local Int is maxJitterUs: 0;
		local Int is startNs: Time:monotonicNs();

		Time:interval(intervalMs: stepMs, count: noteCount, callback: {
			local Int is nowNs: Time:monotonicNs();
			local Int is expectedNs: startNs + ((idx + 1) * stepMs * 1000000);
			local Int is jitterUs: Math:toInt(value: Math:abs(value: ((nowNs - expectedNs) / 1000) as Float));
			if({ jitterUs > maxJitterUs }, {
				maxJitterUs: jitterUs;
			});

			local Int is pick: Math:toInt(value: Math:floor(value: Math:fastRandom() * (scaleMidi:length() as Float)));
			if({ pick >= scaleMidi:length() }, {
				pick: scaleMidi:length() - 1;
			});
			local Int is midi: scaleMidi:get(index: pick, default: 60);
			local Str is noteName: scaleNames:get(index: pick, default: 'C4');
			local Float is freq: synth:midiToFreq(midi: midi);

			local List of Byte is pcm: synth:synthesizeSine(freqHz: freq, durationMs: noteMs, sampleRate: sampleRate);
			if({ audio:isOpen() }, {
				audio:write(samples: pcm);
			});

			notesSec:addLine(
				text: "Note {{idx + 1}}: {{noteName}}",
				color: CleoColor:ansi(code: 252),
				rightText: "{{Math:toInt(value: freq)}} Hz"
			);
			idx: idx + 1;
		});

		if({ audio:isOpen() }, {
			audio:drain();
			audio:close();
		});

		local Int is totalMs: (Time:monotonicNs() - startNs) / 1000000;
		summarySec:addLine(
			text: "Finished in {{totalMs}} ms",
			color: CleoColor:ansi(code: 255),
			rightText: "Max timer jitter: {{maxJitterUs}} us"
		);
		ui:flushFinal();
	}

}
