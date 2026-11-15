#! Random Pentatonic Sine-Wave Tune
#! Exercises high-resolution timing (base:sys:Time, base:sys:DateTime),
#! trigonometry & RNG (base:math:Math), and raw PCM audio (base:audio:Audio).

Class is RandomTune{
	replace Array of Array of String is using: [
		['base', 'sys', as Output()],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'sys', as Time()],
		['base', 'sys', DateTime],
		['base', 'sys', as DateTime()],
		['base', 'math', as Math()],
		['base', 'audio', Audio],
		['base', 'audio', as Audio()],
		['base', 'struct', Array],
		['base', 'struct', List]
	];

	## Synthesizes [durationMs] of stereo 16-bit signed PCM sine wave at [freqHz]
	## with a smooth linear attack/release envelope to prevent clicking.
	local Function of List of Byte is synthesizeSine(Float is freqHz, Int is durationMs, Int is sampleRate){
		local List of Byte is buf;
		local Int is totalSamples: (sampleRate * durationMs) / 1000;
		local Int is fadeSamples: (sampleRate * 15) / 1000;
		local Float is twoPi: 6.283185307179586;
		local Float is amplitude: 12000.0;

		while([Int is i: 0], { i < totalSamples }, {
			local Float is env: 1.0;
			if({ i < fadeSamples }, {
				env: (i as Float) / (fadeSamples as Float);
			});
			if({ i > (totalSamples - fadeSamples) }, {
				env: ((totalSamples - i) as Float) / (fadeSamples as Float);
			});
			local Float is t: (i as Float) / (sampleRate as Float);
			local Float is sampleVal: Math:sin(x: twoPi * freqHz * t) * amplitude * env;
			local Int is s: Math:toInt(x: Math:round(x: sampleVal));
			if({ s < 0 }, {
				s: s + 65536;
			});
			local Int is lo: s & 255;
			local Int is hi: (s >> 8) & 255;

			# Stereo: write Left then Right channel (16-bit little-endian)
			buf:push(lo);
			buf:push(hi);
			buf:push(lo);
			buf:push(hi);
			i: i + 1;
		});
		return buf;
	}

	Function is init(){
		local DateTime is startedAt: DateTime:now();
		Output:line(text: "RandomTune started at " . startedAt:formatIso());

		# C major pentatonic MIDI notes: C4, D4, E4, G4, A4, C5, D5, E5
		local Array of Int is scaleMidi: [60, 62, 64, 67, 69, 72, 74, 76];
		local Array of String is scaleNames: ["C4", "D4", "E4", "G4", "A4", "C5", "D5", "E5"];
		local Int is sampleRate: 44100;
		local Int is noteCount: 12;
		local Int is stepMs: 180;
		local Int is noteMs: 150;

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
			local Float is freq: 440.0 * Math:pow(base: 2.0, exp: ((midi - 69) as Float) / 12.0);

			local List of Byte is pcm: synthesizeSine(freqHz: freq, durationMs: noteMs, sampleRate: sampleRate);
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
