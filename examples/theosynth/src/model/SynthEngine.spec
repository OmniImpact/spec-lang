#! Package theosynth:model
#! Real-time non-blocking polyphonic PCM synthesizer (Sine, Square, Sawtooth).

Class is SynthEngine{
	replace [String] is namespace: ['theosynth', 'model'];

	merge [[String]] is using: [
		['theosynth', 'model', Waveform],
		['base', 'math', [as Math(), Vector]],
		['base', 'struct', List],
		['base', 'audio', as Audio()],
		['base', 'core', SpecError],
		['base', 'sys', [AudioError, as Thread(), as Mem(), as Conditional(), as Loops()]],
		['base', 'sys', 'thread', ThreadScope]
	];

	Int is sampleRate: 22050;
	Int is mutex: 0;
	Boolean is running: false;

	[Int] is voiceMidi: [];
	[Int] is voiceWave: [];
	[Float] is voicePhase: [];
	[Float] is voiceStep: [];
	[Float] is voiceEnv: [];
	[Int] is voiceGate: [];
	[Int] is voiceHoldFrames: [];
	[Int] is voiceRelPending: [];
	Array of Vector is ksBuffers: Array();
	[Int] is ksPos: [];
	[Float] is ksPrev: [];
	Array of Vector is ksBuffers2: Array();
	[Int] is ksPos2: [];
	[Float] is ksPrev2: [];
	Int is ksSeed: 1337;
	Float is normGain: 1.0;

	replace Function is init(){
		mutex: mutexCreate();
	}

	## Converts a [midi] note number (A4 = 69 = 440 Hz) to frequency in Hz.
	Function of Float is midiToFreq(Int is midi){
		return 440.0 * pow(base: 2.0, exp: toFloat(value: midi - 69) / 12.0);
	}

	## Evaluates [wave] at normalized phase [phase] in `[0.0, 1.0)`.
	Function of Float is sampleWave(Waveform is wave, Float is phase){
		if({ wave == Waveform:SQUARE }, {
			if({ phase < 0.5 }, { return 1.0; });
			return -1.0;
		});
		if({ wave == Waveform:SAWTOOTH }, {
			return 2.0 * phase - 1.0;
		});
		return sin(value: 6.283185307179586 * phase);
	}

	local Function of Int is waveToInt(Waveform is w){
		if({ w == Waveform:SQUARE }, { return 1; });
		if({ w == Waveform:SAWTOOTH }, { return 2; });
		if({ w == Waveform:PLUCK }, { return 3; });
		if({ w == Waveform:PIANO }, { return 4; });
		return 0;
	}

	local Function of Float is sampleWaveId(Int is wid, Float is phase){
		if({ wid == 1 }, {
			if({ phase < 0.5 }, { return 1.0; });
			return -1.0;
		});
		if({ wid == 2 }, {
			return 2.0 * phase - 1.0;
		});
		return sin(value: 6.283185307179586 * phase);
	}

	local Function of Vector is makePluckDelayLine(Float is freqHz, Int is rate){
		local Int is delayLen: toInt(value: round(value: toFloat(value: rate) / freqHz));
		if({ delayLen < 2 }, { delayLen: 2; });
		local Vector is dl: Vector(length: delayLen);
		local Int is i: 0;
		while({ i < delayLen }, {
			ksSeed: (ksSeed * 1103515245 + 12345) % 2147483647;
			if({ ksSeed < 0 }, { ksSeed: -ksSeed; });
			local Float is n: (toFloat(value: ksSeed % 20001) / 10000.0) - 1.0;
			dl:set(index: i, value: n);
			i: i + 1;
		});
		return dl;
	}

	## Builds a felt-hammer-filtered Karplus-Strong delay line for Piano voices.
	local Function of Vector is makePianoDelayLine(Float is freqHz, Int is rate){
		local Vector is dl: makePluckDelayLine(freqHz: freqHz, rate: rate);
		local Int is dLen: dl:length();
		# Two-pass moving average models a soft felt hammer strike, blended with warm fundamental.
		local Int is pass: 0;
		while({ pass < 2 }, {
			local Float is prev: dl:get(index: dLen - 1);
			local Int is i: 0;
			while({ i < dLen }, {
				local Float is cur: dl:get(index: i);
				dl:set(index: i, value: 0.5 * (cur + prev));
				prev: cur;
				i: i + 1;
			});
			pass: pass + 1;
		});
		local Int is j: 0;
		local Float is twoPi: 6.283185307179586;
		while({ j < dLen }, {
			local Float is fund: sin(value: twoPi * toFloat(value: j) / toFloat(value: dLen));
			dl:set(index: j, value: 0.65 * dl:get(index: j) + 0.35 * fund);
			j: j + 1;
		});
		return dl;
	}

	## Synthesizes a 16-bit signed little-endian stereo PCM buffer for [wave] at [freqHz].
	Function of List of Byte is synthesize(Waveform is wave, Float is freqHz, Int is durationMs: 160, Int is rate: 22050){
		local List of Byte is buf;
		local Int is totalSamples: (rate * durationMs) / 1000;
		local Int is fadeSamples: (rate * 12) / 1000;
		local Float is amplitude: 11000.0;

		if({ wave == Waveform:PLUCK || wave == Waveform:PIANO }, {
			local Boolean is isPiano: wave == Waveform:PIANO;
			local Vector is dl: if({ isPiano }, { makePianoDelayLine(freqHz: freqHz, rate: rate) }, { makePluckDelayLine(freqHz: freqHz, rate: rate) });
			local Int is dLen: dl:length();
			local Int is pos: 0;
			local Float is prev: dl:get(index: dLen - 1);
			local Float is damp: if({ isPiano }, { 0.9985 }, { 0.996 });
			local Int is ki: 0;
			while({ ki < totalSamples }, {
				local Float is cur: dl:get(index: pos);
				local Float is nextVal: if({ isPiano }, { (0.65 * cur + 0.35 * prev) * damp }, { 0.5 * (cur + prev) * damp });
				dl:set(index: pos, value: nextVal);
				prev: cur;
				pos: pos + 1;
				if({ pos >= dLen }, { pos: 0; });
				local Float is envK: 1.0;
				if({ ki > (totalSamples - fadeSamples) && fadeSamples > 0 }, {
					envK: toFloat(value: totalSamples - ki) / toFloat(value: fadeSamples);
				});
				local Float is sampleK: cur * amplitude * envK;
				pushSample16(outBuf: buf, sample: sampleK);
				pushSample16(outBuf: buf, sample: sampleK);
				ki: ki + 1;
			});
			dl:destroy();
			return buf;
		});

		local Float is phaseStep: freqHz / toFloat(value: rate);
		local Float is phase: 0.0;

		local Int is i: 0;
		while({ i < totalSamples }, {
			local Float is env: 1.0;
			if({ i < fadeSamples && fadeSamples > 0 }, {
				env: toFloat(value: i) / toFloat(value: fadeSamples);
			});
			if({ i > (totalSamples - fadeSamples) && fadeSamples > 0 }, {
				env: toFloat(value: totalSamples - i) / toFloat(value: fadeSamples);
			});
			local Float is val: sampleWave(wave: wave, phase: phase) * amplitude * env;
			local Int is s: toInt(value: round(value: val));
			if({ s < 0 }, { s: s + 65536; });
			local Byte is lo: (s & 255) as Byte;
			local Byte is hi: ((s >> 8) & 255) as Byte;
			buf:push(lo);
			buf:push(hi);
			buf:push(lo);
			buf:push(hi);
			phase: phase + phaseStep;
			if({ phase >= 1.0 }, { phase: phase - 1.0; });
			i: i + 1;
		});
		return buf;
	}

	## Triggers or retriggers [midi] with [wave] without blocking the UI thread.
	Function is noteOn(Int is midi, Waveform is wave){
		local Float is freq: midiToFreq(midi: midi);
		local Float is step: freq / toFloat(value: sampleRate);
		local Int is wid: waveToInt(w: wave);
		local Boolean is isWg: wid == 3 || wid == 4;
		local Vector is newDl: if({ wid == 4 }, {
			makePianoDelayLine(freqHz: freq, rate: sampleRate)
		}, {
			if({ wid == 3 }, { makePluckDelayLine(freqHz: freq, rate: sampleRate) }, { Vector(length: 0) })
		});
		local Vector is newDl2: if({ wid == 4 }, { makePianoDelayLine(freqHz: freq * 1.0015, rate: sampleRate) }, { Vector(length: 0) });
		local Float is initPrev: if({ isWg && newDl:length() > 0 }, { newDl:get(index: newDl:length() - 1) }, { 0.0 });
		local Float is initPrev2: if({ wid == 4 && newDl2:length() > 0 }, { newDl2:get(index: newDl2:length() - 1) }, { 0.0 });
		local Float is initEnv: if({ isWg }, { 1.0 }, { 0.0 });

		mutexLock(handle: mutex);
		local Int is found: -1;
		local Int is i: 0;
		while({ i < voiceMidi:length() && found < 0 }, {
			if({ voiceMidi:get(index: i) == midi }, { found: i; });
			i: i + 1;
		});
		if({ found >= 0 }, {
			ksBuffers:get(index: found):destroy();
			ksBuffers:set(index: found, item: newDl);
			ksPos:set(index: found, item: 0);
			ksPrev:set(index: found, item: initPrev);
			ksBuffers2:get(index: found):destroy();
			ksBuffers2:set(index: found, item: newDl2);
			ksPos2:set(index: found, item: 0);
			ksPrev2:set(index: found, item: initPrev2);
			voiceWave:set(index: found, item: wid);
			voiceStep:set(index: found, item: step);
			if({ isWg }, { voiceEnv:set(index: found, item: 1.0); });
			voiceGate:set(index: found, item: 1);
			voiceHoldFrames:set(index: found, item: 660);
			voiceRelPending:set(index: found, item: 0);
		}, {
			local Int is slot: -1;
			local Int is j: 0;
			while({ j < voiceGate:length() && slot < 0 }, {
				if({ voiceGate:get(index: j) == 0 && voiceEnv:get(index: j) <= 0.001 }, { slot: j; });
				j: j + 1;
			});
			if({ slot >= 0 }, {
				ksBuffers:get(index: slot):destroy();
				ksBuffers:set(index: slot, item: newDl);
				ksPos:set(index: slot, item: 0);
				ksPrev:set(index: slot, item: initPrev);
				ksBuffers2:get(index: slot):destroy();
				ksBuffers2:set(index: slot, item: newDl2);
				ksPos2:set(index: slot, item: 0);
				ksPrev2:set(index: slot, item: initPrev2);
				voiceMidi:set(index: slot, item: midi);
				voiceWave:set(index: slot, item: wid);
				voicePhase:set(index: slot, item: 0.0);
				voiceStep:set(index: slot, item: step);
				voiceEnv:set(index: slot, item: initEnv);
				voiceGate:set(index: slot, item: 1);
				voiceHoldFrames:set(index: slot, item: 660);
				voiceRelPending:set(index: slot, item: 0);
			}, {
				ksBuffers:add(item: newDl);
				ksPos:push(item: 0);
				ksPrev:push(item: initPrev);
				ksBuffers2:add(item: newDl2);
				ksPos2:push(item: 0);
				ksPrev2:push(item: initPrev2);
				voiceMidi:push(item: midi);
				voiceWave:push(item: wid);
				voicePhase:push(item: 0.0);
				voiceStep:push(item: step);
				voiceEnv:push(item: initEnv);
				voiceGate:push(item: 1);
				voiceHoldFrames:push(item: 660);
				voiceRelPending:push(item: 0);
			});
		});
		mutexUnlock(handle: mutex);
	}

	## Begins smooth release of [midi] (respecting minimum attack hold so fast taps still sound).
	Function is noteOff(Int is midi){
		mutexLock(handle: mutex);
		local Int is i: 0;
		while({ i < voiceMidi:length() }, {
			if({ voiceMidi:get(index: i) == midi }, {
				if({ voiceHoldFrames:get(index: i) > 0 }, {
					voiceRelPending:set(index: i, item: 1);
				}, {
					voiceGate:set(index: i, item: 0);
				});
			});
			i: i + 1;
		});
		mutexUnlock(handle: mutex);
	}

	local Function is pushSample16(List of Byte is outBuf, Float is sample){
		local Int is s: toInt(value: round(value: sample));
		if({ s < -32768 }, { s: -32768; });
		if({ s > 32767 }, { s: 32767; });
		if({ s < 0 }, { s: s + 65536; });
		outBuf:push((s & 255) as Byte);
		outBuf:push(((s >> 8) & 255) as Byte);
	}

	## Renders [frames] stereo PCM frames by combining all active voices with equal-power polyphonic normalization.
	Function is mixChunk(List of Byte is outBuf, Int is frames){
		outBuf:clear();
		local Float is attackStep: 1.0 / 176.0;
		local Float is releaseStep: 1.0 / 440.0;
		local Float is amp: 14000.0;

		mutexLock(handle: mutex);
		local Int is nv: voiceMidi:length();
		local Int is fi: 0;
		while({ fi < frames }, {
			local Float is sumL: 0.0;
			local Float is sumR: 0.0;
			local Int is activeCount: 0;
			local Int is vi: 0;
			while({ vi < nv }, {
				local Int is hold: voiceHoldFrames:get(index: vi);
				if({ hold > 0 }, {
					hold: hold - 1;
					voiceHoldFrames:set(index: vi, item: hold);
					if({ hold == 0 && voiceRelPending:get(index: vi) == 1 }, {
						voiceGate:set(index: vi, item: 0);
						voiceRelPending:set(index: vi, item: 0);
					});
				});
				local Int is gate: voiceGate:get(index: vi);
				local Float is env: voiceEnv:get(index: vi);
				if({ gate == 1 }, {
					env: env + attackStep;
					if({ env > 1.0 }, { env: 1.0; });
					voiceEnv:set(index: vi, item: env);
				}, {
					if({ env > 0.0 }, {
						env: env - releaseStep;
						if({ env < 0.0 }, { env: 0.0; });
						voiceEnv:set(index: vi, item: env);
					});
				});
				if({ env > 0.0005 }, {
					local Int is wid: voiceWave:get(index: vi);
					local Float is osc: 0.0;
					if({ wid == 3 || wid == 4 }, {
						local Vector is dl: ksBuffers:get(index: vi);
						local Int is dLen: dl:length();
						if({ dLen >= 2 }, {
							local Int is pos: ksPos:get(index: vi);
							local Float is cur: dl:get(index: pos);
							local Float is prev: ksPrev:get(index: vi);
							local Float is next1: if({ wid == 4 }, { (0.65 * cur + 0.35 * prev) * 0.9985 }, { 0.5 * (cur + prev) * 0.996 });
							dl:set(index: pos, value: next1);
							ksPrev:set(index: vi, item: cur);
							pos: pos + 1;
							if({ pos >= dLen }, { pos: 0; });
							ksPos:set(index: vi, item: pos);
							local Float is sOut: cur;
							if({ wid == 4 }, {
								local Vector is dl2: ksBuffers2:get(index: vi);
								local Int is dLen2: dl2:length();
								if({ dLen2 >= 2 }, {
									local Int is pos2: ksPos2:get(index: vi);
									local Float is cur2: dl2:get(index: pos2);
									local Float is prev2: ksPrev2:get(index: vi);
									dl2:set(index: pos2, value: (0.65 * cur2 + 0.35 * prev2) * 0.9985);
									ksPrev2:set(index: vi, item: cur2);
									pos2: pos2 + 1;
									if({ pos2 >= dLen2 }, { pos2: 0; });
									ksPos2:set(index: vi, item: pos2);
									sOut: 0.5 * (cur + cur2);
								});
							});
							osc: sOut * env;
						});
					}, {
						local Float is ph: voicePhase:get(index: vi);
						osc: sampleWaveId(wid: wid, phase: ph) * env;
						ph: ph + voiceStep:get(index: vi);
						if({ ph >= 1.0 }, { ph: ph - 1.0; });
						voicePhase:set(index: vi, item: ph);
					});
					sumL: sumL + osc;
					sumR: sumR + osc;
					activeCount: activeCount + 1;
				});
				vi: vi + 1;
			});

			local Float is targetGain: if({ activeCount > 1 }, { 1.0 / toFloat(value: activeCount) }, { 1.0 });
			normGain: normGain + (targetGain - normGain) * 0.04;
			local Float is chL: sumL * normGain;
			local Float is chR: sumR * normGain;
			pushSample16(outBuf: outBuf, sample: chL * amp);
			pushSample16(outBuf: outBuf, sample: chR * amp);
			fi: fi + 1;
		});
		mutexUnlock(handle: mutex);
	}

	## Starts the low-latency background audio mixer thread inside [scope].
	Function is startAudio(ThreadScope is scope){
		mutexLock(handle: mutex);
		if({ running }, {
			mutexUnlock(handle: mutex);
			return;
		});
		running: true;
		mutexUnlock(handle: mutex);

		scope:spawn(task: local Function(){
			local String is errMsg: '';
			local Audio is dev: Audio:open(
				sampleRate: sampleRate,
				channels: 2,
				format: 1,
				onError: local Function(SpecError of AudioError is error){
					errMsg: error:description;
				}
			);
			if({ errMsg != '' }, { return; });

			local List of Byte is chunkBuf;
			local Int is chunkFrames: 220;
			while({ true }, {
				mutexLock(handle: mutex);
				local Boolean is keepGoing: running;
				mutexUnlock(handle: mutex);
				if({ !keepGoing }, {
					dev:close();
					return;
				});
				mixChunk(outBuf: chunkBuf, frames: chunkFrames);
				dev:write(samples: chunkBuf, onError: local Function(SpecError of AudioError is _err){});
			});
		});
	}

	Function is close(){
		if({ mutex != 0 }, {
			mutexLock(handle: mutex);
			running: false;
			mutexUnlock(handle: mutex);
		});
	}
}
