# Command Coverage

Status labels: **Implemented** | **Planned** | **Not-applicable** | **Needs-manual-verification**

---

## Common (IEEE 488.2) Commands

| Command | Status | Method |
|---------|--------|--------|
| `*IDN?` | Implemented | `identify()` |
| `*RST` | Implemented | `reset()` |
| `*CLS` | Implemented | `clear_status()` |
| `*OPC?` | Implemented | `operation_complete()` |
| `*WAI` | Implemented | `wait()` |
| `*TRG` | Implemented | `trigger()` |
| `*SAV` | Implemented | `save_state(slot)` |
| `*RCL` | Implemented | `recall_state(slot)` |
| `*TST?` | Implemented | `self_test()` |
| `*OPT?` | Implemented | `get_options()` |
| `*SRE` | Planned | — |
| `*STB?` | Planned | — |
| `*ESE` | Planned | — |
| `*ESR?` | Planned | — |
| `*LRN?` | Planned | — |

---

## Root (`:`) Commands

| Command | Status | Method |
|---------|--------|--------|
| `:AUToscale` | Implemented | `autoscale()` |
| `:DIGitize [chan]` | Implemented | `digitize(*channels)` |
| `:RUN` | Implemented | `run()` |
| `:STOP` | Implemented | `stop()` |
| `:SINGle` | Implemented | `single()` |
| `:VIEW CHANneln` | Implemented | `view(ch)` |
| `:BLANk CHANneln` | Implemented | `blank(ch)` |
| `:AUToscale:AMODE` | Planned | — |
| `:AUToscale:CHANnels` | Planned | — |
| `:STATus` | Planned | — |
| `:SERial` | Not-applicable | Serial number query |
| `:AER?` | Planned | — |
| `:TER?` | Planned | — |
| `:OPEE` / `:OPERegister` | Planned | — |
| `:OVLenable` / `:OVLRegister` | Planned | — |
| `:MTEenable` / `:MTERegister` | Planned | — |

---

## :ACQuire

| Command | Status | Method |
|---------|--------|--------|
| `:ACQuire:TYPE` | Implemented | `acquire_type()` / `acquire_type_query()` |
| `:ACQuire:COUNt` | Implemented | `acquire_count()` / `acquire_count_query()` |
| `:ACQuire:POINts` | Implemented | `acquire_points()` / `acquire_points_query()` |
| `:ACQuire:SRATe?` | Implemented | `acquire_srate_query()` |
| `:ACQuire:COMPlete?` | Implemented | `acquire_complete()` |
| `:ACQuire:MODE` | Planned | — |
| `:ACQuire:SEGMented:COUNt` | Planned | — |
| `:ACQuire:SEGMented:INDex` | Planned | — |
| `:ACQuire:SEGMented:ANALyze` | Planned | — |

---

## :CALibrate

| Command | Status | Method |
|---------|--------|--------|
| `:CALibrate:STATus?` | Planned | — |
| `:CALibrate:DATE?` | Planned | — |
| All others | Not-applicable | Factory/service use |

---

## :CHANnel\<n\>

| Command | Status | Method |
|---------|--------|--------|
| `:CHANnel<n>:DISPlay` | Implemented | `channel_display()` |
| `:CHANnel<n>:COUPling` | Implemented | `channel_coupling()` |
| `:CHANnel<n>:PROBe` | Implemented | `channel_probe()` |
| `:CHANnel<n>:RANGe` | Implemented | `channel_range()` |
| `:CHANnel<n>:SCALe` | Implemented | `channel_scale()` |
| `:CHANnel<n>:OFFSet` | Implemented | `channel_offset()` |
| `:CHANnel<n>:INVert` | Implemented | `channel_invert()` |
| `:CHANnel<n>:LABel` | Implemented | `channel_label()` |
| `:CHANnel<n>:BWLimit` | Implemented | `channel_bwlimit()` |
| `:CHANnel<n>:UNITs` | Implemented | `channel_unit()` |
| `:CHANnel<n>:BANDwidth` | Planned | — |
| `:CHANnel<n>:IMPedance` | Planned | — |
| `:CHANnel<n>:PROTection` | Not-applicable | Read-only hardware flag |
| `:CHANnel<n>:VERNier` | Planned | — |
| `:CHANnel<n>:PROBe:HEAD[:TYPE]` | Planned | — |
| `:CHANnel<n>:PROBe:ID` | Planned | — |
| `:CHANnel<n>:PROBe:SKEW` | Planned | — |
| `:CHANnel<n>:PROBe:STYPe` | Not-applicable | Probe-model specific |

---

## :DISPlay

| Command | Status | Method |
|---------|--------|--------|
| `:DISPlay:PERSistence` | Implemented | `display_persistence()` |
| `:DISPlay:VECTors` | Implemented | `display_vectors()` |
| `:DISPlay:LABel` | Implemented | `display_labels()` |
| `:DISPlay:CLEar` | Implemented | `display_clear()` |
| `:DISPlay:INTensity:WAVeform` | Implemented | `display_intensity()` |
| `:DISPlay:DATA?` | Implemented | `screenshot()` (PNG format) |
| `:DISPlay:ANNotation` | Planned | — |
| `:DISPlay:LABList` | Planned | — |
| `:DISPlay:MENU:TIMeout` | Planned | — |
| `:DISPlay:TRANsparent` | Planned | — |

---

## :DVM

| Command | Status | Method |
|---------|--------|--------|
| `:DVM:ENABle` | Implemented | `dvm_enable()` |
| `:DVM:SOURce` | Implemented | `dvm_source()` |
| `:DVM:MODE` | Implemented | `dvm_mode()` |
| `:DVM:CURRent?` | Implemented | `dvm_current_query()` |
| `:DVM:ARANge` | Planned | — |
| `:DVM:FREQuency?` | Planned | — |

---

## :EXTernal

| Command | Status | Method |
|---------|--------|--------|
| All | Planned | External trigger input configuration |

---

## :FFT

| Command | Status | Method |
|---------|--------|--------|
| `:FFT:DISPlay` | Implemented | `fft_display()` |
| `:FFT:SOURce1` | Implemented | `fft_source()` |
| `:FFT:SPAN` | Implemented | `fft_span()` |
| `:FFT:CENTer` | Implemented | `fft_center()` |
| `:FFT:WINDow` | Implemented | `fft_window()` |
| `:FFT:SCALe` | Implemented | `fft_scale()` |
| `:FFT:REFerence` | Implemented | `fft_reference()` |
| `:FFT:RANGe` | Planned | — |
| `:FFT:OFFSet` | Planned | — |
| `:FFT:VTYPe` | Planned | — |

---

## :HARDcopy

| Command | Status | Method |
|---------|--------|--------|
| `:HARDcopy:INKSaver` | Implemented | used in `screenshot()` |
| `:HARDcopy:STARt` | Planned | — |
| All others | Planned | — |

---

## :MARKer

| Command | Status | Method |
|---------|--------|--------|
| `:MARKer:MODE` | Implemented | `marker_mode()` |
| `:MARKer:X1Position` | Implemented | `marker_x1_position()` |
| `:MARKer:X2Position` | Implemented | `marker_x2_position()` |
| `:MARKer:XDELta?` | Implemented | `marker_xdelta_query()` |
| `:MARKer:YDELta?` | Implemented | `marker_ydelta_query()` |
| `:MARKer:X1Y1source` | Planned | — |
| `:MARKer:X2Y2source` | Planned | — |
| `:MARKer:Y1Position?` | Planned | — |
| `:MARKer:Y2Position?` | Planned | — |
| `:MARKer:XUNits` | Planned | — |
| `:MARKer:YUNits` | Planned | — |

---

## :MEASure

| Command | Status | Method |
|---------|--------|--------|
| `:MEASure:FREQuency?` | Implemented | `measure_frequency()` |
| `:MEASure:PERiod?` | Implemented | `measure_period()` |
| `:MEASure:DUTYcycle?` | Implemented | `measure_duty_cycle()` |
| `:MEASure:VMAX?` | Implemented | `measure_vmax()` |
| `:MEASure:VMIN?` | Implemented | `measure_vmin()` |
| `:MEASure:VPP?` | Implemented | `measure_vpp()` |
| `:MEASure:VRMS?` | Implemented | `measure_vrms()` |
| `:MEASure:VAVerage?` | Implemented | `measure_vaverage()` |
| `:MEASure:VAMPlitude?` | Implemented | `measure_vamplitude()` |
| `:MEASure:VTOP?` | Implemented | `measure_vtop()` |
| `:MEASure:VBASe?` | Implemented | `measure_vbase()` |
| `:MEASure:RISetime?` | Implemented | `measure_risetime()` |
| `:MEASure:FALLtime?` | Implemented | `measure_falltime()` |
| `:MEASure:PHASe?` | Implemented | `measure_phase()` |
| `:MEASure:DELay?` | Implemented | `measure_delay()` |
| `:MEASure:NWIDth?` | Implemented | `measure_nwidth()` |
| `:MEASure:PWIDth?` | Implemented | `measure_pwidth()` |
| `:MEASure:OVERshoot?` | Implemented | `measure_overshoot()` |
| `:MEASure:PREShoot?` | Implemented | `measure_preshoot()` |
| `:MEASure:COUNter?` | Implemented | `measure_counter()` |
| `:MEASure:CLEar` | Implemented | `measure_clear()` |
| `:MEASure:STATistics:DISPlay` | Implemented | `measure_statistics_display()` |
| `:MEASure:STATistics:RESet` | Implemented | `measure_statistics_reset()` |
| `:MEASure:ALL` | Planned | — |
| `:MEASure:BRATe?` | Planned | — |
| `:MEASure:DEFine` | Planned | — |
| `:MEASure:SHOW` | Planned | — |
| `:MEASure:SOURce` | Needs-manual-verification | Source defaults to last set |
| `:MEASure:STATistics:MCOunt` | Planned | — |
| `:MEASure:STATistics:INCRement` | Planned | — |
| `:MEASure:STATistics:RSDeviation?` | Planned | — |
| `:MEASure:RESults?` | Planned | — |
| `:MEASure:TEDGe?` | Planned | — |
| `:MEASure:TAVLue?` | Planned | — |
| `:MEASure:XMAX?` | Planned | — |
| `:MEASure:XMIN?` | Planned | — |
| `:MEASure:WINDow` | Planned | — |

---

## :RECall

| Command | Status | Method |
|---------|--------|--------|
| `:RECall:SETup[:STARt]` | Implemented | (via `system_setup_restore`) |
| Others | Planned | — |

---

## :SAVE

| Command | Status | Method |
|---------|--------|--------|
| `:SAVE:SETup[:STARt]` | Implemented | `save_setup()` |
| `:SAVE:WAVeform[:STARt]` | Implemented | `save_waveform()` |
| `:SAVE:WAVeform:FORMat` | Implemented | (within `save_waveform`) |
| `:SAVE:IMAGe[:STARt]` | Implemented | `save_image()` |
| Others | Planned | — |

---

## :SYSTem

| Command | Status | Method |
|---------|--------|--------|
| `:SYSTem:ERRor?` | Implemented | `system_error_query()` / `check_errors()` |
| `:SYSTem:DATE?` | Implemented | `system_date_query()` |
| `:SYSTem:TIME?` | Implemented | `system_time_query()` |
| `:SYSTem:SETup?` | Implemented | `system_setup_query()` |
| `:SYSTem:SETup` | Implemented | `system_setup_restore()` |
| `:SYSTem:LOCK` | Implemented | `system_lock()` |
| `:SYSTem:DIDentifier?` | Planned | — |
| `:SYSTem:DSP` | Planned | — |
| Others | Planned | — |

---

## :TIMebase

| Command | Status | Method |
|---------|--------|--------|
| `:TIMebase:MODE` | Implemented | `timebase_mode()` |
| `:TIMebase:RANGe` | Implemented | `timebase_range()` |
| `:TIMebase:SCALe` | Implemented | `timebase_scale()` |
| `:TIMebase:POSition` | Implemented | `timebase_position()` |
| `:TIMebase:REFerence` | Implemented | `timebase_reference()` |
| `:TIMebase:VERNier` | Planned | — |
| `:TIMebase:WINDow:POSition` | Planned | — |
| `:TIMebase:WINDow:RANGe` | Planned | — |
| `:TIMebase:WINDow:SCALe` | Planned | — |

---

## :TRIGger

| Command | Status | Method |
|---------|--------|--------|
| `:TRIGger:SWEep` | Implemented | `trigger_sweep()` |
| `:TRIGger:HOLDoff` | Implemented | `trigger_holdoff()` |
| `:TRIGger:HFReject` | Implemented | `trigger_hfreject()` |
| `:TRIGger:NREJect` | Implemented | `trigger_nreject()` |
| `:TRIGger:FORCe` | Implemented | `trigger_force()` |
| `:TRIGger:LEVel:ASETup` | Implemented | `trigger_level_asetup()` |
| `:TRIGger[:EDGE]:SOURce` | Implemented | `trigger_edge_source()` |
| `:TRIGger[:EDGE]:SLOPe` | Implemented | `trigger_edge_slope()` |
| `:TRIGger[:EDGE]:LEVel` | Implemented | `trigger_edge_level()` |
| `:TRIGger[:EDGE]:COUPling` | Implemented | `trigger_edge_coupling()` |
| `:TRIGger[:EDGE]:REJect` | Planned | — |
| `:TRIGger:GLITch:*` | Planned | — |
| `:TRIGger:PATTern:*` | Planned | — |
| `:TRIGger:SHOLd:*` | Planned | — |
| `:TRIGger:TRANsition:*` | Planned | — |
| `:TRIGger:TV:*` | Planned | — |
| `:TRIGger:LEVel:HIGH` | Planned | — |
| `:TRIGger:LEVel:LOW` | Planned | — |
| `:TRIGger:MODE` | Needs-manual-verification | Distinct from SWEep in some contexts |

---

## :WAVeform

| Command | Status | Method |
|---------|--------|--------|
| `:WAVeform:SOURce` | Implemented | `waveform_source()` |
| `:WAVeform:FORMat` | Implemented | `waveform_format()` |
| `:WAVeform:POINts` | Implemented | `waveform_points()` |
| `:WAVeform:PREamble?` | Implemented | `waveform_preamble()` |
| `:WAVeform:DATA?` | Implemented | `waveform_data_raw()` |
| `:WAVeform:XINCrement?` | Implemented | (via preamble) |
| `:WAVeform:XORigin?` | Implemented | (via preamble) |
| `:WAVeform:XREFerence?` | Implemented | (via preamble) |
| `:WAVeform:YINCrement?` | Implemented | (via preamble) |
| `:WAVeform:YORigin?` | Implemented | (via preamble) |
| `:WAVeform:YREFerence?` | Implemented | (via preamble) |
| `:WAVeform:BYTeorder` | Planned | — |
| `:WAVeform:COUNt?` | Planned | — |
| `:WAVeform:POINts:MODE` | Planned | — |
| `:WAVeform:SEGMented:COUNt?` | Planned | Segmented memory |
| `:WAVeform:SEGMented:TTAG?` | Planned | Segmented memory |
| `:WAVeform:SOURce:SUBSource` | Planned | — |
| `:WAVeform:TYPE?` | Planned | — |
| `:WAVeform:UNSigned` | Planned | — |
| `:WAVeform:VIEW` | Planned | — |

---

## Not Implemented (by design for v0.1)

| Subsystem | Reason |
|-----------|--------|
| :ABUS | Analog bus display — requires specific option |
| :DEMO | Training/demo signals only |
| :FRANalysis | G-suffix models only (requires waveform generator) |
| :WGEN | G-suffix models only |
| :MTESt | Option LMT required |
| :SBUS\<n\> | Serial decode — requires license options |
| :LISTer | Serial decode display |

---

## Summary Statistics

| Category | Count |
|----------|-------|
| Implemented | ~85 commands |
| Planned | ~60 commands |
| Not-applicable | ~10 commands |
| Total in manual | ~200+ |
