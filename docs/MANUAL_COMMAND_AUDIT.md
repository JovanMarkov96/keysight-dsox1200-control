# Manual Command Audit

## Source

**Manual:** Keysight InfiniiVision 1200 X-Series and EDUX1052A/G Oscilloscopes Programmer's Guide  
**Revision:** Version 02.12.0000, September 2021  
**Applicable models:** DSOX1202A, DSOX1202G, DSOX1204A, DSOX1204G, EDUX1052A, EDUX1052G  
**Extraction method:** PDF read, table-of-contents and chapter-by-chapter audit

---

## Command Families Identified

The manual organises SCPI commands into 33 chapters (Ch 5–33) plus conceptual chapters.  
Each subsystem below was audited against the table of contents (PDF pages 7–20).

| Chapter | Subsystem | Commands in manual | Notes |
|---------|-----------|-------------------|-------|
| 5  | Common (`*`)         | 15 | IEEE 488.2: *IDN, *RST, *CLS, *OPC, *WAI, *TRG, *SAV, *RCL, *TST, *OPT, *SRE, *STB, *ESE, *ESR, *LRN |
| 6  | Root (`:`)           | 20 | :AUToscale, :DIGitize, :RUN, :STOP, :SINGle, :BLANk, :VIEW, :STATus, :SERial, register commands |
| 7  | :ABUS                | 5  | Analog bus display — not implemented (lab use unlikely) |
| 8  | :ACQuire             | 9  | MODE, TYPE, COUNT, POINts, SRATe, COMPlete, SEGMented variants |
| 9  | :CALibrate           | 8  | DATE, LABel, OUTPut, PROTected, STARt, STATus, TEMPerature, TIME — read-only/factory use |
| 10 | :CHANnel\<n\>        | 16 | BANDwidth, BWLimit, COUPling, DISPlay, IMPedance, INVert, LABel, OFFSet, PROBe, PROTection, RANGe, SCALe, UNITs, VERNier, PROBe:HEAD, PROBe:ID |
| 11 | :DEMO                | 2  | Training signals — not implemented |
| 12 | :DISPlay             | 11 | ANNotation, CLEar, DATA, INTensity, LABel, LABList, MENU:TIMeout, PERSistence, TRANsparent, VECTors |
| 13 | :DVM                 | 6  | ARANge, CURRent, ENABle, FREQuency, MODE, SOURce |
| 14 | :EXTernal            | 8  | BWLimit, DISPlay, LABel, LEVel, POSition, PROBe, RANGe, UNITs |
| 15 | :FFT                 | 9  | CENTer, DISPlay, OFFSet, RANGe, REFerence, SCALe, SOURce1, SPAN, VTYPe, WINDow |
| 16 | :FRANalysis          | 12 | FRA (frequency response) — G-suffix models only, not implemented |
| 17 | :FUNCtion            | 12 | Math waveform: DISPlay, FFT, OFFSet, OPERation, RANGe, REFerence, SCALe, SOURce1/2, GOFT |
| 18 | :HARDcopy            | 11 | AREA, APRinter, FACTors, FFeed, INKSaver, LAYout, NETWork, PALette, PRINter:LIST, STARt |
| 19 | :LISTer              | 3  | Serial decode display — not implemented (low priority) |
| 20 | :MARKer              | 12 | X1/X2/Y1/Y2 cursors, XDELta, YDELta, XUNits, YUNits |
| 21 | :MEASure             | 40+ | Full set: voltage (VMAX, VMIN, VPP, VRMS, VAVerage, VAMPlitude, VTOP, VBASe), time (RISetime, FALLtime, PERiod, FREQuency, DELay, PHASe, DUTYcycle, NWIDth, PWIDth), statistics, OVERshoot, PREShoot, COUNter |
| 22 | :MTESt               | 25+ | Mask test — Option LMT only, not implemented |
| 23 | :RECall              | 5  | FILename, MASK, PWD, SETup, WMEMory |
| 24 | :SAVE                | 15 | FILename, IMAGe, LISTer, MASK, MULTi, PWD, SETup, WAVeform variants, WMEMory |
| 25 | :SBUS\<n\>           | 80+ | Serial decode (I2C, SPI, UART, CAN, LIN) — not implemented |
| 26 | :SYSTem              | 20 | DATE, DIDentifier, DSP, ERRor, LOCK, MENU, PERSona, PRESet, PROTection:LOCK, RLOGger, SETup, TIME, TZONe, USB |
| 27 | :TIMebase            | 9  | MODE, POSition, RANGe, REFerence, SCALe, VERNier, WINDow:POSition/RANGe/SCALe |
| 28 | :TRIGger             | 40+ | EDGE, GLITch, PATTern, SHOLd, TRANsition, TV trigger types; FORCe, HOLDoff, HFReject, NREJect, SWEep, LEVel, LEVel:ASETup |
| 29 | :WAVeform            | 16 | BYTeorder, COUNt, DATA, FORMat, POINts, POINts:MODE, PREamble, SEGMented, SOURce, SOURce:SUBSource, TYPE, UNSigned, VIEW, XINCrement, XORigin, XREFerence, YINCrement, YORigin, YREFerence |
| 30 | :WGEN                | 25+ | Waveform generator — G-suffix models only, not implemented |
| 31 | :WMEMory\<r\>        | 4  | Reference waveforms |
| 32 | Obsolete/Discontinued | — | Listed but not implemented |
| 33 | Error messages       | — | Full list used for CommandError codes |

---

## Implementation Decisions

### High confidence — implemented from manual evidence

1. **:WAVeform preamble scaling** (PDF p. 48)  
   The manual states preamble returns 10 comma-separated fields in the order:  
   `format, type, points, count, x_increment, x_origin, x_reference, y_increment, y_origin, y_reference`  
   Voltage conversion: `V = (raw - y_reference) × y_increment + y_origin`  
   Time conversion: `t = (index - x_reference) × x_increment + x_origin`

2. **:DIGitize vs :SINGle** (PDF p. 42–43)  
   `:DIGitize` is the recommended capture command for programmatic use — it clears the buffer, acquires, and stops.  
   `:SINGle` arms for one acquisition without blocking; polled with `:ACQuire:COMPlete?`.  
   Driver uses `:DIGitize` in `capture_waveform()` with extended timeout.

3. **:TIMebase:MODE must be MAIN for :DIGitize** (PDF p. 48, NOTE)  
   If MODE is ROLL, XY, or WINDow, `:DIGitize` returns "Settings conflict".  
   Driver's `configure_timebase()` defaults to MAIN; `acquisition()` context manager explicitly sets MAIN.

4. **Binary block waveform transfer** (PDF p. 50–51)  
   IEEE 488.2 definite-length block format: `#` + digit-count + byte-count + data.  
   pyvisa `query_binary_values()` handles this automatically. BYTE format (uint8) is fastest; WORD (int16, big-endian) gives full 12-bit resolution.

5. **Error queue: :SYSTem:ERRor?** (PDF p. 581)  
   Returns `code,"message"` pairs. Code 0 = no error. Driver reads until 0.

6. **Probe attenuation affects range** (PDF p. 46, example)  
   `:CHANnel1:PROBe 10` + `:CHANnel1:RANGe 16` = 1.6 V on-screen (probe-compensated).  
   All range/scale values are in probe-compensated volts.

### Gaps discovered

| Gap | Decision |
|-----|----------|
| :ABUS (analog bus) | Not implemented — requires option and specific setup |
| :FRANalysis | Not implemented — G-suffix (built-in waveform generator) models only |
| :WGEN | Not implemented — G-suffix models only |
| :MTESt | Not implemented — Option LMT only |
| :SBUS\<n\> | Not implemented — serial decode requires license options |
| :WMEMory\<r\> save/recall | Partially covered via :SAVE/:RECall methods |
| :DISPlay:DATA? | Implemented as `screenshot()` method using PNG format |
| Segmented memory | :ACQuire:SEGMented commands noted but not implemented in v0.1 |

---

## Evidence Lines Referenced

- PDF p. 3 (Table 1): model numbers, channel count, bandwidth, memory  
- PDF p. 42–43: initialise → capture → analyse flow; :DIGitize semantics  
- PDF p. 46: channel setup example (probe, range, offset, coupling)  
- PDF p. 46: timebase setup example (range, delay, reference)  
- PDF p. 47: trigger setup example (sweep, level, slope)  
- PDF p. 47–48: :ACQuire subsystem in example; point count, average count  
- PDF p. 48 (NOTE): TIMebase:MODE MAIN requirement for :DIGitize  
- PDF p. 50–51: binary block data format; definite-length block encoding  
- PDF p. 53: Telnet socket access on port 5024 (prompt) / 5025 (no prompt)  
- PDF p. 37: USB device and LAN interfaces are always active  
