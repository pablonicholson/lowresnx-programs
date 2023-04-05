#!/usr/bin/python3
"""
Imports image files into characters and bg.
"""
import sys
import PIL.Image

def getroms(fp, skip=()):
	num = []
	nam = []
	dat = []

	st = 0
	fp.seek(0)
	for line in fp:
		line = line.translate(str.maketrans("", "", "\t\n\r "))
		if st:
			if line.startswith("#"):
				st = 0
			else:
				dat[-1] += line

		if line.startswith("#"):
			n, s = line[1:].split(":")
			if not int(n) in skip:
				st = 1
				num.append(int(n))
				nam.append(s)
				dat.append("")
	fp.close()
	return [num, nam, dat]

def putroms(fp, roms):
	nl = 0
	fp.seek(0)
	while 1:
		pos = fp.tell()
		line = fp.readline()
		if not line:
			nl = 1
			break
		if line[0] == "#":
			break
	fp.seek(pos)
	if nl:
		fp.write("\n")

	for rom in sorted(zip(*roms)):
		fp.write("#%d:%s\n" % (rom[0], rom[1]))
		fp.write(rom[2])
		fp.write("\n")
	fp.truncate()
	fp.close()

def getchr(chr, im):
	pixels = im.load()
	width, height = im.size

	for sy in range(0, height, 8):
		for sx in range(0, width, 8):
			c = 0
			for y in range(8):
				for x in range(8):
					p = pixels[7 - x + sx, 7 - y + sy]
					c |= ((p & 1) << x + 64 | (p >> 1 & 1) << x) << y * 8
			chr.append(c)

def getbg(bg, chr, pal, im):
	pixels = im.load()
	width, height = im.size

	chr.append(0)

	bg.append(0)
	bg.append(0)
	bg.append(width // 8)
	bg.append(height // 8)

	for sy in range(0, height, 8):
		for sx in range(0, width, 8):
			c1 = c2 = c3 = c4 = 0
			for y in range(8):
				for x in range(8):
					p1 = pixels[7 - x + sx, 7 - y + sy]
					p2 = pixels[    x + sx, 7 - y + sy]
					p3 = pixels[7 - x + sx,     y + sy]
					p4 = pixels[    x + sx,     y + sy]
					c1 |= ((p1 & 1) << x + 64 | (p1 >> 1 & 1) << x) << y * 8
					c2 |= ((p2 & 1) << x + 64 | (p2 >> 1 & 1) << x) << y * 8
					c3 |= ((p3 & 1) << x + 64 | (p3 >> 1 & 1) << x) << y * 8
					c4 |= ((p4 & 1) << x + 64 | (p4 >> 1 & 1) << x) << y * 8
			if c1 in chr:
				bg.append(chr.index(c1))
				bg.append(pal | 0x00)
			elif c2 in chr:
				bg.append(chr.index(c2))
				bg.append(pal | 0x08)
			elif c3 in chr:
				bg.append(chr.index(c3))
				bg.append(pal | 0x10)
			elif c4 in chr:
				bg.append(chr.index(c4))
				bg.append(pal | 0x18)
			else:
				bg.append(len(chr))
				bg.append(pal | 0x00)
				chr.append(c1)

def savechr(chr, nrom, lrom):
	s = ""
	for c in chr:
		s += "%032X" % c
	lrom[0].append(nrom)
	lrom[1].append("CHR")
	lrom[2].append(s)

def savebg(bg, nrom, lrom):
	s = ""
	for c in bg:
		s += "%02X" % c
	lrom[0].append(nrom)
	lrom[1].append("BG")
	lrom[2].append(s)

def loadim(fname):
	im = PIL.Image.open(fname)
	im = im.convert("P", dither=0, palette=1, colors=4)
	return im

def importchr(nxfile, imfile, chrom, bgrom, palrom, palidx):
	fp = open(nxfile, "a+")
	roms = getroms(fp, skip=[chrom])

	im = loadim(imfile)

	lchr = []
	getchr(lchr, im)

	if len(lchr) > 256:
		sys.exit("error: invalid image size")

	savechr(lchr, chrom, roms)

	fp = open(nxfile, "r+")
	putroms(fp, roms)

def importbg(nxfile, imfile, chrom, bgrom, palrom, palidx):
	fp = open(nxfile, "a+")
	roms = getroms(fp, skip=[chrom, bgrom])

	if palidx > 7 or palidx < 0:
		sys.exit("error: invalid palette index")

	im = loadim(imfile)

	lbg = []
	lchr = []
	getbg(lbg, lchr, palidx, im)

	w = lbg[2]
	h = lbg[3]

	if (w * h) > 4096 or (w * h) < 80:
		sys.exit("error: invalid image size")

	if len(lchr) > 256:
		sys.exit("error: invalid image size")

	savechr(lchr, chrom, roms)
	savebg(lbg, bgrom, roms)

	fp = open(nxfile, "r+")
	putroms(fp, roms)

if __name__ == "__main__":
	if len(sys.argv) < 3:
		sys.exit("usage: %s <nxfile> <imagefile> [chrom [bgrom [palrom [palidx]]]]" % sys.argv[0])
	else:
		nxfile = sys.argv[1]
		imfile = sys.argv[2]
	if len(sys.argv) > 3:
		chrom = int(sys.argv[3])
	else:
		chrom = 2
	if len(sys.argv) > 4:
		bgrom = int(sys.argv[4])
	else:
		bgrom = -1
	if len(sys.argv) > 5:
		palrom = int(sys.argv[5])
	else:
		palrom = 1
	if len(sys.argv) > 6:
		palidx = int(sys.argv[6])
	else:
		palidx = 0

	if bgrom == -1:
		importchr(nxfile, imfile, chrom, bgrom, palrom, palidx)
	else:
		importbg(nxfile, imfile, chrom, bgrom, palrom, palidx)
