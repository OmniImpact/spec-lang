#! Random Pentatonic Sine-Wave Tune
#! Exercises high-resolution timing (base:sys:Time, base:sys:DateTime),
#! trigonometry & RNG (base:math:Math), and raw PCM audio (base:audio:Audio).

Class is RandomTune{

	replace Array of Array of String is using: [
		['base', 'sys', as Output()],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Time()],
		['base', 'sys', DateTime],
		['base', 'sys', as DateTime()],
		['base', 'math', as Math()],
		['base', 'audio', Audio],
		['base', 'audio', as Audio()],
		['base', 'struct', Array],
		['base', 'struct', List],
		[Synth]
	];

	Function is init(){
		local DateTime is startedAt: DateTime:now();
		Output:line(text: "RandomTune started at " . startedAt:formatIso());

		local Array of Int is scaleMidi: [60, 62, 64, 67, 69, 72, 74, 76];
		local Array of String is scaleNames: ["C4", "D4", "E4", "G4", "A4", "C5", "D5", "E5"];
		local Int is sampleRate: 44100;
		local Int is noteCount: 12;
		local Int is stepMs: 180;
		local Int is noteMs: 150;
		local Synth is synth: Synth:init();

		local Audio is audio: Audio:open(sampleRate: sampleRate, channels: 2, format: 1);
		if({ !audio:isOpen() }, {
			Output:line(text: "Audio device unavailable; running silent timing & synthesis pass.");
		});

		local Int is idx: 0;
		local Int is maxJitterUs: 0;
		local Int is startNs: Time:monotonicNs();

		Time:interval(intervalMs: stepMs, count: noteCount, callback: {
			local Int is nowNs: Time:monotonicNs();
			local Int is expectedNs: startNs + ((idx + 1) * stepMs * 1000000);
			local Int is jitterUs: Math:toInt(x: Math:abs(value: ((nowNs - expectedNs) / 1000) as Float));
			if({ jitterUs > maxJitterUs }, {
				maxJitterUs: jitterUs;
			});

			local Int is pick: Math:toInt(x: Math:floor(x: Math:fastRandom() * (scaleMidi:length() as Float)));
			if({ pick >= scaleMidi:length() }, {
				pick: scaleMidi:length() - 1;
			});
			local Int is midi: scaleMidi:get(index: pick, default: 60);
			local String is noteName: scaleNames:get(index: pick, default: "C4");
			local Float is freq: synth:midiToFreq(midi: midi);

			local List of Byte is pcm: synth:synthesizeSine(freqHz: freq, durationMs: noteMs, sampleRate: sampleRate);
			if({ audio:isOpen() }, {
				audio:write(samples: pcm);
			});

			Output:line(text: "  Note " . ((idx + 1) as String) . ": " . noteName . " (" . (Math:toInt(x: freq) as String) . " Hz)");
			idx: idx + 1;
		});

		if({ audio:isOpen() }, {
			audio:drain();
			audio:close();
		});

		local Int is totalMs: (Time:monotonicNs() - startNs) / 1000000;
		Output:line(text: "Finished in " . (totalMs as String) . " ms (max timer jitter: " . (maxJitterUs as String) . " us)");
	}

}
