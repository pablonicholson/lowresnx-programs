#!/usr/bin/python3
"""
Exports characters and bg into image files.
"""
import sys
import PIL.Image

defpal = [
	0x053f2f00, 0x00383400,
	0x003c0c00, 0x003f3c00,
	0x003f2a15, 0x003f2a15,
	0x003f2a15, 0x003f2a15
]

def loadrom(fp, nrom, mlen):
	lout = []
	sbuf = ""
	st = 0

	fp.seek(0)
	for line in fp:
		line = line.translate(str.maketrans("", "", "\t\n\r "))
		if st:
			if line.startswith("#"):
				break

			sbuf += line
			while len(sbuf) >= mlen:
				lout.append(int(sbuf[:mlen], 16))
				sbuf = sbuf[mlen:]

		if line.startswith("#") and int(line[1:].split(":")[0]) == nrom:
			st = 1
	return lout

def putchr(chr, im):
	pixels = im.load()

	sx = sy = 0
	for c in chr:
		for y in range(8):
			for x in range(8):
				hi = c >> (x + y * 8) & 1
				lo = c >> (x + y * 8 + 64) & 1
				pixels[7 - x + sx, 7 - y + sy] = lo | hi << 1
		sx += 8
		if sx >= 128:
			sy += 8
			sx = 0

def putbg8(bg, chr, im):
	pixels = im.load()
	width, height = im.size

	sx = sy = 0
	for i, c in enumerate(bg):
		if i < 4 or i % 2:
			continue

		if (i + 1) >= len(bg):
			sys.exit("error: invalid bg data")
		if c >= len(chr):
			sys.exit("error: invalid character data")

		for y in range(8):
			for x in range(8):
				hi = chr[c] >> (x + y * 8) & 1
				lo = chr[c] >> (x + y * 8 + 64) & 1

				flp = bg[i + 1] & 0x18
				pal = bg[i + 1] & 0x07

				px = (lo | hi << 1) + pal * 4
				if flp == 0x00:
					pixels[7 - x + sx, 7 - y + sy] = px
				elif flp == 0x08:
					pixels[    x + sx, 7 - y + sy] = px
				elif flp == 0x10:
					pixels[7 - x + sx,     y + sy] = px
				elif flp == 0x18:
					pixels[    x + sx,     y + sy] = px
		sx += 8
		if sx >= width:
			sy += 8
			sx = 0

def putbg16(bg, chr, im):
	pixels = im.load()
	width, height = im.size

	sx = sy = 0
	for i, c in enumerate(bg):
		if i < 4 or i % 2:
			continue

		if (i + 1) >= len(bg):
			sys.exit("error: invalid bg data")
		if (c + 17) >= len(chr):
			sys.exit("error: invalid character data")

		for y in range(16):
			for x in range(16):
				ch = c
				dx, dy = 0, 0
				if x > 7:
					ch += 1
					dx = 8
				if y > 7:
					ch += 16
					dy = 8
				hi = chr[ch] >> (x % 8 + y % 8 * 8) & 1
				lo = chr[ch] >> (x % 8 + y % 8 * 8 + 64) & 1

				flp = bg[i + 1] & 0x18
				pal = bg[i + 1] & 0x07

				px = (lo | hi << 1) + pal * 4
				if flp == 0x00:
					pixels[7 - x % 8 + sx + dx, 7 - y % 8 + sy + dy] = px
				elif flp == 0x08:
					pixels[x % 8 + sx + 8 - dx, 7 - y % 8 + sy + dy] = px
				elif flp == 0x10:
					pixels[7 - x % 8 + sx + dx, y % 8 + sy + 8 - dy] = px
				elif flp == 0x18:
					pixels[x % 8 + sx + 8 - dx, y % 8 + sy + 8 - dy] = px
		sx += 16
		if sx >= width:
			sy += 16
			sx = 0

def putnpal(pal, npal, im):
	lclr = []
	for nclr in range(4):
		if nclr == 0:
			rgb = pal[0] >> 24 & 0xff
		else:
			rgb = pal[npal] >> (24 - nclr * 8) & 0xff
		lclr.append((rgb >> 4 & 3) * 80 + 15)
		lclr.append((rgb >> 2 & 3) * 80 + 15)
		lclr.append((rgb      & 3) * 80 + 15)
	im.putpalette(lclr)

def putpal(pal, im):
	lclr = []
	for npal, p in enumerate(pal):
		for nclr in range(4):
			if nclr == 0:
				rgb = pal[0] >> 24 & 0xff
			else:
				rgb = p >> (24 - nclr * 8) & 0xff
			lclr.append((rgb >> 4 & 3) * 80 + 15)
			lclr.append((rgb >> 2 & 3) * 80 + 15)
			lclr.append((rgb      & 3) * 80 + 15)
	lclr += [0] * (768 - len(lclr))
	im.putpalette(lclr)

def saveim(im, fname):
	if fname.lower().endswith((".png", ".gif", ".bmp")):
		im.save(fname)
	else:
		im.save(fname + ".png")

def exportchr(nxfile, imfile, chrom, bgrom, palrom, palidx):
	fp = open(nxfile, "r")
	lpal = loadrom(fp, palrom, 8)
	lchr = loadrom(fp, chrom, 32)

	if palidx > 7 or palidx < 0:
		sys.exit("error: invalid palette index")

	if len(lchr) > 256:
		sys.exit("error: invalid character data")

	if len(lpal) <= palidx:
		lpal = defpal

	im = PIL.Image.new("P", (128, 128))

	putnpal(lpal, palidx, im)
	putchr(lchr, im)

	saveim(im, imfile)

def exportbg(nxfile, imfile, chrom, bgrom, palrom, palidx):
	fp = open(nxfile, "r")
	lpal = loadrom(fp, palrom, 8)
	lchr = loadrom(fp, chrom, 32)
	lbg = loadrom(fp, bgrom, 2)

	if len(lbg) < 4:
		sys.exit("error: invalid bg data")

	if len(lpal) < 8:
		lpal = defpal

	tsize = 8 + lbg[1] * 8
	w = lbg[2]
	h = lbg[3]

	if (w * h) > 4096 or (w * h) < 80:
		sys.exit("error: invalid bg data")

	if len(lbg) > (w * h * 2 + 4):
		sys.exit("error: invalid bg data")

	im = PIL.Image.new("P", (w * tsize, h * tsize))

	putpal(lpal, im)
	if tsize == 8:
		putbg8(lbg, lchr, im)
	elif tsize == 16:
		putbg16(lbg, lchr, im)
	else:
		sys.exit("error: invalid bg data")

	saveim(im, imfile)

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
		exportchr(nxfile, imfile, chrom, bgrom, palrom, palidx)
	else:
		exportbg(nxfile, imfile, chrom, bgrom, palrom, palidx)
