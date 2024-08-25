try:
  from WICPy import *
except:
  from wic import *
import os.path
import msvcrt
import array
import threading

path = os.path.dirname(os.path.abspath(globals().get('__file__', ' '))) + r'\test'

Initialize()

#IWICImagingFactory instance creation opt1
WICImagingFactoryClassFactory = IClassFactory(IWICImagingFactory.CLSID)
IImagingFactory = WICImagingFactoryClassFactory.CreateInstance(IWICImagingFactory)
print(IImagingFactory, IImagingFactory.Release())
WICImagingFactoryClassFactory.Release()

#IWICImagingFactory instance creation opt2
IImagingFactory = IWICImagingFactory()

#IStream & IWICStream handling
#Creating IStream from file
p = path + r'\test.jpg'
IStream = IStream.CreateOnFile(p)
#Reading into a bytearray
IStream.Seek(2)
b = bytearray(10)
IStream.Read(b, 4)
print(b[:4])
#Emptying a file
p2 = path + r'\test-.jpg'
IStream2 = IStream.CreateOnFile(p2, 'write')
IStream2.Release()
#Writing to file
IStream2 = IStream.CreateOnFile(p2, 'readwrite')
IStream2.Write(b, 4)
print(IStream2.GetContent())
IStream2.Release()
#Copying to file
IStream2 = IStream.CreateOnFile(p2, 'write')
print(IStream.CopyTo(IStream2, IStream.Seek(0, 'end') + IStream.Seek(0, 'beginning')))
IStream2.Release()
#Copying to memory
IStream2 = IStream.CreateInMemory(b'COPY')
print(IStream2.Seek(0, 'end'), IStream.CopyTo(IStream2, IStream.Seek(0, 'end') + IStream.Seek(0, 'beginning')), IStream2.Seek(0, 'end'))
#Cloning
IStream3 = IStream2.Clone()
b = bytearray(20)
b[0:3] = b'PAD'
#Reading into a memoryview
m = memoryview(b)[3:7]
IStream3.Seek(0, 'beginning')
IStream3.Read(m)
print(m.tobytes(), b)
IStream3.Release()
IStream2.Release()
#Creating IWICStream from IStream
IWStream = IImagingFactory.CreateStream()
IWStream.InitializeFromIStream(IStream)
print(IWStream.Seek(0, 'end'))
IWStream.Release()
IWStream = IImagingFactory.CreateStream()
IWStream.InitializeFromIStreamRegion(IStream, 100, IStream.Seek(0, 'end') - 200)
print(IWStream.Seek(0, 'end'))
IWStream.Release()
#Creating IWICStream from memory
IWStream = IImagingFactory.CreateStream()
IWStream.InitializeFromMemory(m)
print(IWStream.GetContent())
IWStream.Release()
#Creating IWICStream from file
IWStream = IImagingFactory.CreateStream()
IWStream.InitializeFromFilename(p2, 0x80000000)
#Reading into an array
IWStream.Seek(6)
a = array.array('B', b'\x00' * 4)
IWStream.Read(a)
print(a.tobytes())
#Reading into a bytes (albeit immutable...)
b = b'\x00' * 4
IWStream.Seek(-4)
IWStream.Read(b)
print(b)
IWStream.Release()
IStream.Release()

#Decoding and encoding with color context change
#Decoding from a file handle
f = open(p, 'rb')
h = msvcrt.get_osfhandle(f.fileno())
IDecoder = IImagingFactory.CreateDecoderFromFileHandle(h, metadata_option='onload')
#Retrieving format
print(IDecoder.GetContainerFormat())
IBitmapFrame = IDecoder.GetFrame(0)
#Retrieving contexts
IColorContexts = IBitmapFrame.GetColorContexts()
#Creating a dci-p3 color context from file
IColorContext1 = IImagingFactory.CreateColorContext()
IColorContext1.InitializeFromFilename(path + r'\sDCIP3.col')
#Creating an uncalibrated exif color context
IColorContext2 = IImagingFactory.CreateColorContext()
IColorContext2.InitializeFromExifColorSpace('uncalibrated')
#Changing color context
IColorTransform = IImagingFactory.CreateColorTransformer()
IColorTransform.Initialize(IBitmapFrame, IColorContexts[0], IColorContext1, '24bppBGR')
#Encoding to a file with the new color contexts
p2 = path + r'\test-.jpg'
IStream2 = IStream.CreateOnFile(p2, 'write')
IEncoder = IImagingFactory.CreateEncoder('jpeg')
IEncoder.Initialize(IStream2)
IBitmapFrameEncode, IEncoderOptions = IEncoder.CreateNewFrame()
IBitmapFrameEncode.Initialize()
IBitmapFrameEncode.SetColorContexts((IColorContext1, IColorContext2))
IBitmapFrameEncode.WriteSource(IColorTransform)
IBitmapFrameEncode.Commit()
IEncoder.Commit()
#Releasing interfaces
tuple(map(IUnknown.Release, (IEncoder, IBitmapFrameEncode, IStream2, IColorTransform, IColorContext2, IColorContext1, *IColorContexts, IBitmapFrame, IDecoder)))
f.close()
#Decoding from a stream specifying format
p = path + r'\test-p3.jpg'
IStream1 = IImagingFactory.CreateStream()
IStream1.InitializeFromFilename(p)
#Error handling
IDecoder = IImagingFactory.CreateDecoder('jpdg')
print('jpdg ->', IGetLastError())
IDecoder = IImagingFactory.CreateDecoder('jpg')
#Retrieving decoder capabilities
print(IDecoder.QueryCapability(IStream1))
IDecoder.Release()
#Decoding from a stream relying on format detection
IDecoder = IImagingFactory.CreateDecoderFromStream(IStream1, metadata_option='onload')
#Retrieving format
f = IDecoder.GetContainerFormat()
print(f.guid.to_string(), f, ' - ', IDecoder.GetFrameCount(), 'frame')
#Releasing interfaces
IDecoder.Release()
IStream1.Release()

#Decoded frame examination
IDecoder = IImagingFactory.CreateDecoderFromFilename(p, metadata_option='onload')
IBitmapFrame = IDecoder.GetFrame(0)
#Retrieving size, resolution and pixel format
print(IBitmapFrame.GetSize(), IBitmapFrame.GetResolution(), IBitmapFrame.GetPixelFormat())
#Retrieving pixels in a 2d memoryview
b = bytearray(7 * 5 * 3)
m = memoryview(b).cast('B', (5, 7 * 3))
IBitmapFrame.CopyPixels((0, 0, 7, 5), 7 * 3, m)
for l in range(5):
  print(' '.join('(%d, %d, %d)' % (m[l, 3 * c], m[l, 3 * c + 1], m[l, 3 * c + 2]) for c in range(7)))
#Retrieving color contexts and comparing to color context initialized with the same type and content
IColorContexts = IBitmapFrame.GetColorContexts()
for cc in IColorContexts:
  t = cc.GetType()
  if t == 'ExifColorSpace':
    s = cc.GetExifColorSpace()
    print(t, s)
    cc2 = IImagingFactory.CreateColorContext()
    cc2.InitializeFromExifColorSpace(s)
    print(cc2.GetExifColorSpace() == s)
    cc2.Release()
  elif t == 'Profile':
    b = cc.GetProfileBytes()
    print(t, b)
    cc2 = IImagingFactory.CreateColorContext()
    cc2.InitializeFromMemory(b)
    print(cc2.GetProfileBytes() == b)
    cc2.Release()

#Metadata management (read)
#Reading metadata
IMetadataQueryReader = IBitmapFrame.GetMetadataQueryReader()
#Enumeratng metadata
e = IMetadataQueryReader.GetEnumerator()
print(e.Next(2))
e2 = e.Clone()
e2.Reset()
e2.Skip(2)
print(e2.Next(40))
e2.Release()
e.Reset()
print(*e)
e.Release()
#Retrieving root metadata infos
print(IMetadataQueryReader.GetLocation(), IMetadataQueryReader.GetContainerFormat().name, IMetadataQueryReader.GetMetadataNames())
#Retrieving app1 metadata in a new reader
IMetadataQueryReader2 = IMetadataQueryReader.GetMetadataByName('/app1')
print(IMetadataQueryReader2.GetLocation(), IMetadataQueryReader2.GetContainerFormat().name, IMetadataQueryReader2.GetMetadataNames())
#Retrieving nested metadata from the previous reader
print(IMetadataQueryReader2.GetMetadataWithTypeByName('/ifd/exif/{ushort=36864}'))
#Error handling
IMetadataQueryReader3 = IMetadataQueryReader2.GetMetadataByName('/ifd/gps/no')
print('/ifd/gps/no ->', IGetLastError())
#Retrieving gps metadata from the previous reader
IMetadataQueryReader3 = IMetadataQueryReader2.GetMetadataByName('/ifd/gps')
print(IMetadataQueryReader2.GetMetadataTypeByName('/ifd/gps'), IMetadataQueryReader3.GetMetadataWithTypeByName('/{ushort=2}'), IMetadataQueryReader3.GetMetadataWithTypeByName('/{ushort=3}'))
print('%02.f° %02.f\' %02.2f"' % MetadataFloatFraction.from_rational(IMetadataQueryReader3.GetMetadataByName('/{ushort=2}')), IMetadataQueryReader3.GetMetadataByName('/{ushort=1}').decode(), ' - ', '%02.f° %02.f\' %02.2f"' % MetadataFloatFraction.from_rational(IMetadataQueryReader3.GetMetadataByName('/{ushort=4}')), IMetadataQueryReader3.GetMetadataByName('/{ushort=3}').decode())
#Releasing interfaces
IMetadataQueryReader3.Release()
IMetadataQueryReader2.Release()
IMetadataQueryReader.Release()

#Retrieving thumbnail
IBitmapThumbnail = IBitmapFrame.GetThumbnail()
print(IBitmapThumbnail.GetSize())
IBitmapThumbnail.Release()

#Parsing metadata recursively
print('metadata:')
IMetadataQueryReader = IBitmapFrame.GetMetadataQueryReader()
st = [(IMetadataQueryReader, IMetadataQueryReader.GetEnumerator())]
stc = st[0]
r = IMetadataQueryReader
while True:
  n = next(stc[1], None)
  if n is not None:
    m = r.GetMetadataWithTypeByName(n)
    if m[0] == 13:
      r = m[1]
      stc = (r, r.GetEnumerator())
      st.append(stc)
    else:
      print(r.GetLocation() + n, '(', m[0].vtype, ',', m[1][:] if  m[0] & 4096 else m[1], ')')
  else:
    st.pop()
    if st:
      stc = st[-1]
      r = stc[0]
    else:
      break
del stc
print('end - metadata')
#Accessing predefined metadata
for q in (*IMetadataQueryReader.__class__._queries, 'Resolution', 'Position'):
  if q != 'ThumbnailBytes':
    m = getattr(IMetadataQueryReader, 'Get' + q)()
    if isinstance(m, ctypes.Array):
      m = m[:]
    elif isinstance(m, IWICMetadataQueryReader):
      m = '%s [%s]' % (m, m.GetContainerFormat().name)
    if m is not None:
      print(q, ':', m)
IMetadataQueryReader.Release()

#Bitmap manipulation
#Creation from the decoded frame
IBitmapCache = IImagingFactory.CreateBitmapFromSource(IBitmapFrame, 'ondemand')
print(IBitmapCache.GetSize())
#Setting resolution
IBitmapCache.SetResolution(50,50)
print(IBitmapCache.GetResolution())
#Locking an area to access it
IBitmapLock = IBitmapCache.Lock((0, 0, 7, 5), 'readwrite')
s = IBitmapLock.GetStride()
#Retrieving size and pixel format, and exploring the format and comparison possibilities of guid / code properties
f = IBitmapLock.GetPixelFormat()
print(IBitmapLock.GetSize(), f, f.guid, f.name, f == f.name, f== f.guid)
#Reading the content in an array of bytes
b = IBitmapLock.GetDataPointer()
for l in range(5):
  print(' '.join('(%d, %d, %d)' % (b[l * s + 3 * c], b[l * s + 3 * c + 1], b[l * s + 3 * c + 2]) for c in range(7)))
#Swapping the components of the first pixel
b[0:3] = b[2::-1]
IBitmapLock.Release()
#Creation from an area of the decoded frame
IBitmapCache2 = IImagingFactory.CreateBitmapFromSourceRect(IBitmapCache, (0,0,2,2))
#Retrieving the content in a bytearray
b2 = bytearray(3)
IBitmapCache2.CopyPixels((0, 0, 1, 1), 3, b2)
print('(%d, %d, %d)' % tuple(b2))
IBitmapCache2.Release()
#Creation from an array of bytes
IBitmapCache2 = IImagingFactory.CreateBitmapFromMemory(7, 5, f, s, b)
#Retrieving the content in a bytearray
b2 = bytearray(3)
IBitmapCache2.CopyPixels((0, 0, 1, 1), 3, b2)
print('(%d, %d, %d)' % tuple(b2))
IBitmapCache2.Release()
#Creation of an empty bitmap
IBitmapCache2 = IImagingFactory.CreateBitmap(7, 5, f)
#Writing from a bytearray to the bitmap after locking the area
IBitmapLock2 = IBitmapCache2.Lock((0, 0, 7, 5), 'write')
s2 = IBitmapLock2.GetStride()
b2 = IBitmapLock2.GetDataPointer()
b = bytearray(7 * 5 * 3)
IBitmapFrame.CopyPixels((0, 0, 7, 5), 7 * 3, b)
b_ = ctypes.addressof((ctypes.c_char * len(b)).from_buffer(b))
b2_ = ctypes.addressof(b2)
for l in range(5):
  ctypes.memmove(b2_ + l * s2, b_ + l * 7 * 3, 7 * 3)
IBitmapLock2.Release()
#Reading in a bytearray
b2 = bytearray(len(b2))
IBitmapCache2.CopyPixels((0, 0, 7, 5), s2, b2)
for l in range(5):
  print(' '.join('(%d, %d, %d)' % (b2[l * s2 + 3 * c], b2[l * s2+ 3 * c + 1], b2[l * s2 + 3 * c + 2]) for c in range(7)))
IBitmapCache2.Release()
IBitmapCache.Release()
#Creation from an icon handle
user32 = ctypes.WinDLL('user32', use_last_error=True)
user32.LoadIconW.restype = wintypes.HICON
IBitmap = IImagingFactory.CreateBitmapFromHICON(user32.LoadIconW(None, wintypes.LPCWSTR(32516)))
print(IBitmap.GetSize(), IBitmap.GetPixelFormat())
#Creation from a bitmap handle
gdiplus = ctypes.WinDLL('gdiplus', use_last_error=True)
token = ctypes.wintypes.ULONG()
gdiplus.GdiplusStartup(ctypes.byref(token), ctypes.c_char_p(ctypes.string_at(ctypes.addressof(ctypes.c_uint(1)), ctypes.sizeof(ctypes.c_uint)) + b'\x00' * 24), None)
Bitmap = ctypes.c_void_p()
gdiplus.GdipCreateBitmapFromFile(wintypes.LPCWSTR(path + r'\test.png'), ctypes.byref(Bitmap))
HBitmap = wintypes.HBITMAP()
gdiplus.GdipCreateHBITMAPFromBitmap(Bitmap, ctypes.byref(HBitmap))
IBitmap = IImagingFactory.CreateBitmapFromHBITMAP(HBitmap)
print(IBitmap.GetSize(), IBitmap.GetPixelFormat())
gdiplus.GdipDisposeImage(Bitmap)
gdiplus.GdiplusShutdown(token)
IBitmap.Release()

#Encoding options management
p2 = path + r'\test-p3-.jpg'
IStream2 = IStream.CreateOnFile(p2, 'write')
IEncoder = IImagingFactory.CreateEncoder('jpeg')
IEncoder.Initialize(IStream2)
IBitmapFrameEncode, IEncoderOptions = IEncoder.CreateNewFrame()
print(IEncoderOptions.CountProperties())
#Retrieving available properties
properties = IEncoderOptions.GetPropertyInfo()
print(properties)
#Retrieving properties values
print(IEncoderOptions.Read(properties))
#or
print(IEncoderOptions.GetProperties())
#Setting simple properties values
IEncoderOptions.Write({'ImageQuality': ('VT_R4', 0.95), 'JpegYCrCbSubsampling': ('VT_UI1', 3)})
#or
IEncoderOptions.SetProperties({'ImageQuality': 0.95, 'JpegYCrCbSubsampling': 3})
print(IEncoderOptions.Read({'ImageQuality': 'VT_R4', 'JpegYCrCbSubsampling': 'VT_UI1'}))
#Setting array properties values from a 2d memoryview on top an array (simulating)
b = array.array('l', (16, 11, 10, 16, 24, 40, 51, 61,
12, 12, 14, 19, 26, 58, 60, 55,
14, 13, 16, 24, 40, 57, 69, 56,
14, 17, 22, 29, 51, 87, 80, 62,
18, 22, 37, 56, 68, 109, 103, 77,
24, 35, 55, 64, 81, 104, 113, 92,
49, 64, 78, 87, 103, 121, 120, 101,
72, 92, 95, 98, 112, 100, 103, 99))
l = memoryview(b).cast('B').cast('l', (8, 8))
IEncoderOptions.Write({'Luminance': ('VT_ARRAY | VT_I4', l)})
lu = IEncoderOptions.Read({'Luminance': 'VT_ARRAY'})
print(lu)
lu = lu['Luminance'][1]
for i in range(8):
  print(lu[i][:])
l = memoryview(lu)
l = l.cast('B').cast(l.format.lstrip('<>@'), (8,8))
for i in range(8):
  print(', '.join(str(l[i,j]) for j in range(8)))
#Setting array property value from the right 1d array using the name as an object field
IEncoderOptions.Luminance = b
print(IEncoderOptions.Luminance[:])
#Initializing the frame encoder with the options
IBitmapFrameEncode.Initialize(IEncoderOptions)
#Setting the color context
IBitmapFrameEncode.SetColorContexts((*IColorContexts,))
#Clipping the bitmap
IBitmapClipper = IImagingFactory.CreateBitmapClipper()
IBitmapClipper.Initialize(IBitmapFrame, (200, 500, 400, 300))
#Rescaling the clipped bitmap
IBitmapScaler = IImagingFactory.CreateBitmapScaler()
IBitmapScaler.Initialize(IBitmapClipper, 200, 150, 'fant')
#Rotating and flipping the rescaled clipped bitmap after caching it
IBitmapCache = IImagingFactory.CreateBitmapFromSource(IBitmapScaler, 'ondemand')
IBitmapFlipRotator = IImagingFactory.CreateBitmapFlipRotator()
IBitmapFlipRotator.Initialize(IBitmapCache, 'FlipHorizontal | Rotate90')
print(IBitmapFlipRotator.GetSize())
#Setting the size of the encoded frame
IBitmapFrameEncode.SetSize(130,130)
#Setting the pixel format of the encoded frame
print(IBitmapFrameEncode.SetPixelFormat('8bppGray'))
#Setting the resolution of the encoded frame
IBitmapFrameEncode.SetResolution(72, 72)
#Rescaling again to use as thumbnail
IBitmapScaler2 = IImagingFactory.CreateBitmapScaler()
IBitmapScaler2.Initialize(IBitmapFlipRotator, 20, 15, 'fant')
IBitmapFrameEncode.SetThumbnail(IBitmapScaler2)

#Metadata management (write)
#Retrieving a writer for the frame to be encoded
IMetadataQueryWriter = IBitmapFrameEncode.GetMetadataQueryWriter()
print(IMetadataQueryWriter.GetMetadataNames())
#Creating a writer initialized from a reader
IMetadataQueryReader = IBitmapFrame.GetMetadataQueryReader()
IMetadataQueryReader2 = IMetadataQueryReader.GetMetadataByName('/app1/ifd/gps')
IMetadataQueryWriter1 = IImagingFactory.CreateQueryWriterFromReader(IMetadataQueryReader2)
print(IMetadataQueryWriter1.GetContainerFormat(), IMetadataQueryWriter1.GetMetadataNames())
#Keeping only a metadata in the writer
for name in IMetadataQueryWriter1.GetMetadataNames():
  if name != '/{ushort=4}':
    IMetadataQueryWriter1.RemoveMetadataByName(name)
print(IMetadataQueryWriter1.GetMetadataNames())
IMetadataQueryReader2.Release()
IMetadataQueryReader.Release()
#Setting metadata values
IMetadataQueryWriter1.SetMetadataByName('/{ushort=4}', ('VT_VECTOR | VT_UI8', MetadataFloatFraction.to_rational((0, 0, 0))))
IMetadataQueryWriter1.SetMetadataByName('/{ushort=1}', ('VT_LPSTR', b'N'))
IMetadataQueryWriter1.SetMetadataByName('/{ushort=2}', ('VT_VECTOR | VT_UI8', MetadataFloatFraction.to_rational(('4300/100', '5000/100', '2010/100'))))
#Rebuilding the metadata tree
IMetadataQueryWriter2 = IImagingFactory.CreateQueryWriter('ifd')
IMetadataQueryWriter2.SetMetadataByName('/gps', ('VT_UNKNOWN', IMetadataQueryWriter1))
IMetadataQueryWriter3 = IImagingFactory.CreateQueryWriter('app1')
IMetadataQueryWriter3.SetMetadataByName('/ifd', ('VT_UNKNOWN', IMetadataQueryWriter2))
IMetadataQueryWriter.SetMetadataByName('/app1', ('VT_UNKNOWN', IMetadataQueryWriter3))
print(IMetadataQueryWriter.GetMetadataNames(), IMetadataQueryWriter3.GetMetadataNames(), IMetadataQueryWriter2.GetMetadataNames(), IMetadataQueryWriter1.GetMetadataNames())
#Setting metadata value directly from its path
IMetadataQueryWriter.SetMetadataByName('/app1/ifd/gps/{ushort=3}', ('VT_LPSTR', b'E'))

#Encoding finalization
#Writing pixels in the frame
IBitmapFrameEncode.WritePixels(10, 130, b'\xff' * (130 * 10))
#Converting the pixel format to grayscale
IFormatConverter = IImagingFactory.CreateFormatConverter()
print('24bppBGR -> 8bppGray :', IFormatConverter.CanConvert('24bppBGR', '8bppGray'))
IFormatConverter.Initialize(IBitmapFlipRotator, '8bppGray', 'errordiffusion')
#Adding the converted bitmap to the frame
IBitmapFrameEncode.WriteSource(IFormatConverter, (10,5,130,190))
#Encoding the frame
IBitmapFrameEncode.Commit()
#Encoding the image
IEncoder.Commit()
#Releasing interfaces
tuple(map(IUnknown.Release, (IBitmapFrameEncode, IEncoderOptions, IFormatConverter, IBitmapScaler2, IBitmapFlipRotator, IBitmapCache, IBitmapScaler, IBitmapClipper, IMetadataQueryWriter, IMetadataQueryWriter3, IMetadataQueryWriter2, IMetadataQueryWriter1, IEncoder, IStream2, *IColorContexts)))

#Fast metadata modification
IDecoder2 = IImagingFactory.CreateDecoderFromFilename(p2,  desired_access='readwrite', metadata_option='ondemand')
IBitmapFrame2 = IDecoder2.GetFrame(0)
print(IBitmapFrame2.GetSize(), IBitmapFrame2.GetResolution(), tuple(map(IWICColorContext.GetType, IBitmapFrame2.GetColorContexts())), IBitmapFrame2.GetPixelFormat().name)
IBitmapThumbnail = IBitmapFrame2.GetThumbnail()
print(IBitmapThumbnail.GetSize())
IBitmapThumbnail.Release()
#Retrieving the fast metadata writer
IFastMetadataEncoder = IImagingFactory.CreateFastMetadataEncoderFromFrameDecode(IBitmapFrame2)
IMetadataQueryWriter = IFastMetadataEncoder.GetMetadataQueryWriter()
#Setting the value of an existing metadata
IMetadataQueryWriter.SetLongitude(('500/100', '1000/100', '8120/100'))
IFastMetadataEncoder.Commit()
IMetadataQueryWriter.Release()
IFastMetadataEncoder.Release()
#Reading the metadata
IMetadataQueryReader = IBitmapFrame2.GetMetadataQueryReader()
print(IMetadataQueryReader.GetMetadataNames())
IMetadataQueryReader2 = IMetadataQueryReader.GetMetadataByName('/app1/ifd')
print(IMetadataQueryReader2.GetMetadataNames())
print(IMetadataQueryReader2.GetPosition())
#Releasing interfaces
tuple(map(IUnknown.Release, (IMetadataQueryReader2, IMetadataQueryReader, IBitmapFrame2, IDecoder2, IStream2, IBitmapFrame, IDecoder)))

#Palette manipulation
p = path + r'\test.png'
IDecoder = IImagingFactory.CreateDecoderFromFilename(p, metadata_option='onload')
f = IDecoder.GetContainerFormat()
print(f.guid.to_bytes(), f, ' - ', IDecoder.GetFrameCount(), 'frame')
IBitmapFrame = IDecoder.GetFrame(0)
print(IBitmapFrame.GetSize(), IBitmapFrame.GetResolution(), IBitmapFrame.GetPixelFormat().name)
print(IBitmapFrame.GetColorContexts())
#Retrieving the palette
IPalette = IBitmapFrame.GetPalette()
print(IPalette.GetType(), IPalette.GetColorCount(), IPalette.IsBlackWhite(), IPalette.IsGrayscale(), IPalette.HasAlpha())
#reading the colors from the palette
print(*('%08X' % c for c in IPalette.GetColors()), sep=', ')
#Creating a new palette initialized from the previous one
IPalette2 = IImagingFactory.CreatePalette()
IPalette2.InitializeFromPalette(IPalette)
print(*('%08X' % c for c in IPalette2.GetColors()), sep=', ')
#Creating a new palette initialized from a predefined format
IPalette2.InitializePredefined('FixedHalftone256')
print(*('%08X' % c for c in IPalette2.GetColors()), sep=', ')
#Creating a new customized palette
IPalette2.InitializeCustom(IPalette.GetColors())
print(*('%08X' % c for c in IPalette2.GetColors()), sep=', ')
#Creating a new palette initialized from the decoded frame
IPalette2.InitializeFromBitmap(IBitmapFrame, 256)
print(*('%08X' % c for c in IPalette2.GetColors()), sep=', ')
#Creating a new palette initialized from a predefined format
IPalette2.InitializePredefined('FixedGray256')
#Converting the palette of the decoded frame
IFormatConverter = IImagingFactory.CreateFormatConverter()
IFormatConverter.Initialize(IBitmapFrame, IBitmapFrame.GetPixelFormat().name, 'DualSpiral8x8', IPalette2, 1, 'FixedGray256')
#Encoding the converted bitmap to a file
p2 = path + r'\test-.png'
IStream2 = IStream.CreateOnFile(p2, 'write')
IEncoder = IImagingFactory.CreateEncoder('png')
IEncoder.Initialize(IStream2)
IBitmapFrameEncode, IEncoderOptions = IEncoder.CreateNewFrame()
properties = IEncoderOptions.GetPropertyInfo()
print(properties)
print(IEncoderOptions.Read(properties))
IEncoderOptions.FilterOption = 4
print(IEncoderOptions.GetPropertiesWithType())
IBitmapFrameEncode.Initialize(IEncoderOptions)
IBitmapFrameEncode.SetPalette(IPalette2)
IBitmapFrameEncode.WriteSource(IFormatConverter)
IBitmapFrameEncode.Commit()
IEncoder.Commit()
#Releasing interfaces
tuple(map(IUnknown.Release, (IEncoder, IBitmapFrameEncode, IEncoderOptions, IFormatConverter, IPalette2, IPalette, IBitmapFrame, IDecoder, IStream2)))

#Geotiff reading
#Decoding a 16-bit signed short geotiff elevation file
p = path + r'\test.tif'
IDecoder = IImagingFactory.CreateDecoderFromFilename(p)
f = IDecoder.GetContainerFormat()
print(f.guid, f.name, ' - ', IDecoder.GetFrameCount(), 'frame')
IBitmapFrame = IDecoder.GetFrame(0)
w, h = IBitmapFrame.GetSize()
print('(%d, %d)' % (w, h), IBitmapFrame.GetResolution(), IBitmapFrame.GetPixelFormat().name)
#Retrieving metadata
IMetadataQueryReader = IBitmapFrame.GetMetadataQueryReader()
for n in ('BitsPerSample', 'Compression', 'SamplesPerPixel', 'SampleFormat', 'Predictor', 'ImageWidth', 'ImageLength'):
  print('%s: %s' % (n, getattr(IMetadataQueryReader, 'Get' + n)()))
IMetadataQueryReader.Release()
#Retrieving the elevations in a int16 memoryview on top a bytearray
b=bytearray(w*h*2)
m=memoryview(b).cast('h', (w, h))
IBitmapFrame.CopyPixels(None, w*2, m)
print(*(m[0,c] for c in range(w)))
IBitmapFrame.Release()
IDecoder.Release()

#Applying transformations at decoding stage
p = path + r'\test.jpg'
IDecoder = IImagingFactory.CreateDecoderFromFilename(p)
IBitmapFrame = IDecoder.GetFrame(0)
#Creating the source transformer
IBitmapSourceTransform = IBitmapFrame.GetBitmapSourceTransform()
#Checking capabilities
print(IBitmapSourceTransform.GetClosestSize(900,500))
print(IBitmapSourceTransform.GetClosestPixelFormat('8bppGray'))
print(IBitmapSourceTransform.DoesSupportTransform('Rotate90'))
#Retrieving the transformed bitmap in a bytearray
b=bytearray(960*540*4)
print(IBitmapSourceTransform.CopyPixels((0,0,960,540), 960,540,'24bppBGR', 'Rotate0', 960*4, b))
IBitmapSourceTransform.Release()
IBitmapFrame.Release()
IDecoder.Release()

#Metadata handling through block rather than queries (read)
p = path + r'\test.jpg'
IDecoder = IImagingFactory.CreateDecoderFromFilename(p)
IBitmapFrame = IDecoder.GetFrame(0)
#Creating the block reader from the decoded frame
IMetadataBlockReader = IBitmapFrame.GetMetadataBlockReader()
print(IMetadataBlockReader.GetContainerFormat(), IMetadataBlockReader.GetCount())
#Enumerating the metadata containers
print(*map(IWICMetadataReader.GetMetadataFormat, IMetadataBlockReader.GetEnumerator()))
#Creating a reader upon the first container
IMetadataReader = IMetadataBlockReader.GetReaderByIndex(0)
print(IMetadataReader.GetMetadataFormat(), IMetadataReader.GetCount())
#Enumerating the metadata with their type
e = IMetadataReader.GetEnumeratorWithType()
siv = e.Next(IMetadataReader.GetCount())
print(siv)
# Retrieving a metadata from its schema and identifier
print(IMetadataReader.GetValue(*siv[0][:2]).GetMetadataFormat())
# Retrieving a metadata from its index
siv = IMetadataReader.GetValueByIndex(0)
print(siv[2].GetMetadataFormat())
del siv

#Jpeg manipulation (part 1)
#Creating a jpeg frame decoder from the decoded frame
IJpegFrameDecode = IBitmapFrame.GetJpegFrameDecode()
#Handling indexing
print(IJpegFrameDecode.DoesSupportIndexing())
IJpegFrameDecode.SetIndexing('load')
#Retrieving the frame header
print(IJpegFrameDecode.GetFrameHeader())
#Retrieving the tables
print(dict(map(lambda kv: (kv[0], kv[1][:]), IJpegFrameDecode.GetDcHuffmanTable(0, 0).items())))
print(dict(map(lambda kv: (kv[0], kv[1][:]), IJpegFrameDecode.GetDcHuffmanTable(0, 1).items())))
print(dict(map(lambda kv: (kv[0], kv[1][:]), IJpegFrameDecode.GetAcHuffmanTable(0, 0).items())))
print(dict(map(lambda kv: (kv[0], kv[1][:]), IJpegFrameDecode.GetAcHuffmanTable(0, 1).items())))
print(IJpegFrameDecode.GetQuantizationTable(0, 0)[:])
print(IJpegFrameDecode.GetQuantizationTable(0, 1)[:])
#Retrieving the scan header
print(IJpegFrameDecode.GetScanHeader(0))
#Retrieving the compressed data
b = IJpegFrameDecode.CopyScan(0)
#Creating an encoder to a new file
p2 = path + r'\test-.jpg'
IStream2 = IStream.CreateOnFile(p2, 'write')
IEncoder = IImagingFactory.CreateEncoder('jpeg', 'Microsoft')
IEncoder.Initialize(IStream2)
IBitmapFrameEncode, IEncoderOptions = IEncoder.CreateNewFrame()
print(IEncoderOptions.GetProperties())
#Setting the tables accordingly to the decoded frame ones
IEncoderOptions.SetProperties({'JpegYCrCbSubsampling': IJpegFrameDecode.GetFrameHeader()['SampleFactors'].name[-3:], 'Luminance': IJpegFrameDecode.GetQuantizationTable(0, 0), 'Chrominance': IJpegFrameDecode.GetQuantizationTable(0, 1), 'JpegLumaAcHuffmanTable': IJpegFrameDecode.GetAcHuffmanTable(0,0), 'JpegLumaDcHuffmanTable': IJpegFrameDecode.GetDcHuffmanTable(0,0), 'JpegChromaAcHuffmanTable': IJpegFrameDecode.GetAcHuffmanTable(0,1), 'JpegChromaDcHuffmanTable': IJpegFrameDecode.GetDcHuffmanTable(0,1), 'SuppressApp0': True})
print('Luminance:', IEncoderOptions.Luminance[:])
print('Chrominance:', tuple(IEncoderOptions.Read({'Chrominance': 'VT_ARRAY | VT_I4'}).values())[0][1][:])
IBitmapFrameEncode.Initialize(IEncoderOptions)
#Setting the sze and pixel format accordingly to the decoded frame
IBitmapFrameEncode.SetSize(*IBitmapFrame.GetSize())
print(IBitmapFrameEncode.SetPixelFormat(IBitmapFrame.GetPixelFormat()))

#Metadata handling through block rather than queries (write)
#Creating the block writer for the frame to be encoded
IMetadataBlockWriter = IBitmapFrameEncode.GetMetadataBlockWriter()
print(IMetadataBlockWriter.GetContainerFormat(), IMetadataBlockWriter.GetCount())
#Retrieving the writers from the block writer and enumerating their content
IMetadataWriters = IMetadataBlockWriter.GetWriters()
for IMetadataWriter in IMetadataWriters:
  print(IMetadataWriter.GetMetadataFormat(), IMetadataWriter.GetCount())
  e = IMetadataWriter.GetEnumerator()
  print(e.Next(IMetadataWriter.GetCount()))
  IMetadataWriter.Release()
#Retrieving a writer by its index
IMetadataWriter = IMetadataBlockWriter.GetWriterByIndex(0)
#Retrieving a metadata value by its index
v = IMetadataWriter.GetValueWithTypeByIndex(0)
print(v)
#Setting a metadata value by its index
IMetadataWriter.SetValueByIndex(0, *v[:2], (v[2][0],4000))
print(IMetadataWriter.GetValueByIndex(0))
IMetadataWriter.SetValueByIndex(0, *v)
print(IMetadataWriter.GetValueByIndex(0))
#Setting a metadata value by its schema and identifier
for i in (2, 3):
  v=(IMetadataWriter.GetValueWithTypeByIndex(i))
  IMetadataWriter.SetValue(*v[:2], (v[2][0], 72))
print(IMetadataWriter.GetValueByIndex(2), IMetadataWriter.GetValueByIndex(3))
#Initializing the block writer from the block reader of the decoded frame
IMetadataBlockWriter.InitializeFromBlockReader(IMetadataBlockReader)
#Retrieving a writer by its index
IMetadataWriter = IMetadataBlockWriter.GetWriterByIndex(0)
print(IMetadataWriter.GetMetadataFormat())
#Retrieving a nested writer by its index
IMetadataWriter2 = IMetadataWriter.GetValueByIndex(0)[2]
print(IMetadataWriter2.GetMetadataFormat(), *IMetadataWriter2.GetEnumerator())
#Reading, setting and removing metadata in the writer
e = tuple(IMetadataWriter2.GetEnumeratorWithType())
print(IMetadataWriter2.GetValue(*e[2][:2]))
IMetadataWriter2.SetValue(*e[2][:2], (e[2][2][0], 5))
print(IMetadataWriter2.GetValue(*e[2][:2]))
IMetadataWriter2.SetValue(*e[2][:2], e[2][2])
print(IMetadataWriter2.GetValue(*e[2][:2]))
IMetadataWriter2.SetValue(('VT_EMPTY', None), ('VT_UI2', 315), ('VT_LPSTR', b'artist'))
print(IMetadataWriter2.GetValue(('VT_EMPTY', None), ('VT_UI2', 315)))
IMetadataWriter2.RemoveValue(('VT_EMPTY', None), ('VT_UI2', 315))
#Removing a writer from the block writer
print(IMetadataBlockWriter.GetWriters())
IMetadataBlockWriter.RemoveWriterByIndex(0)
#Adding a writer to the block writer
print(IMetadataBlockWriter.GetWriters())
IMetadataBlockWriter.AddWriter(IMetadataWriter)
#Removing a writer from the block writer
print(IMetadataBlockWriter.GetWriters())
IMetadataBlockWriter.RemoveWriterByIndex(0)
#Adding a writer to the block writer at a defined index
IMetadataBlockWriter.SetWriterByIndex(0, IMetadataWriter)
#Removing a writer from the block writer
IMetadataBlockWriter.RemoveWriterByIndex(0)

#Jpeg manipulation (part 2)
# IBitmapFrameEncode.SetColorContexts(IBitmapFrame.GetColorContexts())
#Creating a jpeg frame encoder for the frame to be encoded
IJpegFrameEncode = IBitmapFrameEncode.GetJpegFrameEncode()
#Checking the quantization tables
print('Luminance:', IJpegFrameDecode.GetQuantizationTable(0, 0)[:])
print('Chrominance:', IJpegFrameDecode.GetQuantizationTable(0, 1)[:])
#Writing the compressed data from the jpeg decoded frame witout reencoding
print(dict(map(lambda kv: (kv[0], kv[1][:]), IJpegFrameEncode.GetDcHuffmanTable(0).items())))
print(dict(map(lambda kv: (kv[0], kv[1][:]), IJpegFrameEncode.GetDcHuffmanTable(1).items())))
print(dict(map(lambda kv: (kv[0], kv[1][:]), IJpegFrameEncode.GetAcHuffmanTable(0).items())))
print(dict(map(lambda kv: (kv[0], kv[1][:]), IJpegFrameEncode.GetAcHuffmanTable(1).items())))
print(IJpegFrameEncode.GetQuantizationTable(0)[:])
print(IJpegFrameEncode.GetQuantizationTable(1)[:])
IJpegFrameEncode.WriteScan(b)
IBitmapFrameEncode.Commit()
IEncoder.Commit()
#Releasing interfaces
tuple(map(IUnknown.Release, (IEncoder, IJpegFrameEncode, IBitmapFrameEncode, IEncoderOptions, IStream2, IJpegFrameDecode, IBitmapFrame, IDecoder, IMetadataBlockWriter, IMetadataWriter2, IMetadataWriter, IMetadataReader, IMetadataBlockReader)))

#Component infos manipulation
#IWICComponentFactory instance creation
IComponentFactory = IWICComponentFactory()
#Enumerating components
print(*(c.GetComponentType() for c in IComponentFactory.CreateComponentEnumerator(options='BuiltInOnly')))
p = path + r'\test.jpg'
IStream = IStream.CreateOnFile(p)
#Enumerating decoders
for d in IComponentFactory.CreateComponentEnumerator('decoder'):
  print(d.GetComponentType().name, d.GetCLSID().name, d.GetSigningStatus().name, d.GetAuthor(), d.GetVendorGUID().name, d.GetVersion(), d.GetSpecVersion(), d.GetFriendlyName(), d.GetContainerFormat().name, tuple(f.name for f in d.GetPixelFormats()), d.GetColorManagementVersion(), d.GetDeviceManufacturer(), d.GetDeviceModels(), d.GetMimeTypes(), d.GetFileExtensions(), d.DoesSupportAnimation(), d.DoesSupportChromaKey(), d.DoesSupportLossless(), d.DoesSupportMultiframe(), d.MatchesMimeType('image/jpeg'), d.GetPatterns(), d.MatchesPattern(IStream))
  if d.GetCLSID() == 'JpegDecoder':
    dj = d
  else:
    d.Release()
IStream.Release()
#Creating a decoder instance from a decoder info
print(dj.CreateInstance())
del dj
#Enumerating encoders
for e in IComponentFactory.CreateComponentEnumerator('encoder'):
  print(e.GetComponentType().name, e.GetCLSID().name, e.GetSigningStatus().name, e.GetAuthor(), e.GetVendorGUID().name, e.GetVersion(), e.GetSpecVersion(), e.GetFriendlyName(), e.GetContainerFormat().name, tuple(f.name for f in e.GetPixelFormats()), e.GetColorManagementVersion(), e.GetDeviceManufacturer(), e.GetDeviceModels(), e.GetMimeTypes(), e.GetFileExtensions(), e.DoesSupportAnimation(), e.DoesSupportChromaKey(), e.DoesSupportLossless(), e.DoesSupportMultiframe(), e.MatchesMimeType('image/jpeg'), sep=' - ')
  e.Release()
#Enumerating pixel format converters
for c in IComponentFactory.CreateComponentEnumerator('PixelFormatConverter'):
  print(c.GetComponentType().name, c.GetCLSID().name, c.GetSigningStatus().name, c.GetAuthor(), c.GetVendorGUID().name, c.GetVersion(), c.GetSpecVersion(), c.GetFriendlyName(), tuple(f.name for f in c.GetPixelFormats()), sep=' - ')
  c.Release()
#Enumerating pixel formats
for f in IComponentFactory.CreateComponentEnumerator('PixelFormat'):
  print(f.GetComponentType().name, f.GetCLSID().name, f.GetSigningStatus().name, f.GetAuthor(), f.GetVendorGUID().name, f.GetVersion(), f.GetSpecVersion(), f.GetFriendlyName(), f.GetFormatGUID().name, f.GetBitsPerPixel(), f.GetChannelCount(), tuple(f.GetChannelMask(i) for i in range(f.GetChannelCount())), f.SupportsTransparency(), f.GetNumericRepresentation().name, getattr(f.GetColorContext(), 'GetType', lambda : None)(), sep=' - ')
  f.Release()
#Enumerating metadata readers
for m in IComponentFactory.CreateComponentEnumerator('MetadataReader'):
  print(m.GetComponentType().name, m.GetCLSID().name, m.GetSigningStatus().name, m.GetAuthor(), m.GetVendorGUID().name, m.GetVersion(), m.GetSpecVersion(), m.GetFriendlyName(), m.GetMetadataFormat().name, tuple(f.name for f in m.GetContainerFormats()), m.GetDeviceManufacturer(), m.GetDeviceModels(), m.DoesRequireFullStream(), m.DoesSupportPadding(), m.DoesRequireFixedSize(), tuple((f.name, m.GetPatterns(f)) for f in m.GetContainerFormats()), sep=' - ')
  m.Release()
#Enumerating metadata writers
for m in IComponentFactory.CreateComponentEnumerator('MetadataWriter'):
  print(m.GetComponentType().name, m.GetCLSID().name, m.GetSigningStatus().name, m.GetAuthor(), m.GetVendorGUID().name, m.GetVersion(), m.GetSpecVersion(), m.GetFriendlyName(), m.GetMetadataFormat().name, tuple(f.name for f in m.GetContainerFormats()), m.GetDeviceManufacturer(), m.GetDeviceModels(), m.DoesRequireFullStream(), m.DoesSupportPadding(), m.DoesRequireFixedSize(), tuple((f.name, m.GetHeader(f)) for f in m.GetContainerFormats()), sep=' - ')
  m.Release()
#Creating a decoder from its type
print(IComponentFactory.CreateComponentInfo('JpegDecoder').GetFriendlyName())
IDecoder = IComponentFactory.CreateDecoder('jpeg', 'Microsoft')
print(IDecoder.GetDecoderInfo().GetVendorGUID().name)
IDecoder.Release()
#Creating an encoder from its type
IEncoder = IComponentFactory.CreateEncoder('jpeg')
print(IEncoder.GetEncoderInfo().GetCLSID().name)
IEncoder.Release()
#Creating a metadata query reader from a block reader
p = path + r'\test.jpg'
IDecoder = IComponentFactory.CreateDecoderFromFilename(p, metadata_option='ondemand')
IBitmapFrame = IDecoder.GetFrame(0)
IMetadataBlockReader = IBitmapFrame.GetMetadataBlockReader()
IMetadataQueryReader = IComponentFactory.CreateQueryReaderFromBlockReader(IMetadataBlockReader)
print(IMetadataQueryReader.GetLocation(), IMetadataQueryReader.GetMetadataNames())
#Creating a metadata query writer from a block writer
p2 = path + r'\test-.jpg'
IStream2 = IStream.CreateOnFile(p2, 'readwrite')
IEncoder = IComponentFactory.CreateEncoder('jpeg')
IEncoder.Initialize(IStream2)
IBitmapFrameEncode, IEncoderOptions = IEncoder.CreateNewFrame()
IBitmapFrameEncode.Initialize()
IMetadataBlockWriter = IBitmapFrameEncode.GetMetadataBlockWriter()
IMetadataBlockWriter.InitializeFromBlockReader(IMetadataBlockReader)
#Creating a metadata writer for the block writer
IMetadataQueryWriter = IComponentFactory.CreateQueryWriterFromBlockWriter(IMetadataBlockWriter)
print(IMetadataQueryWriter.GetLocation(), IMetadataQueryWriter.GetMetadataNames())
#Retrieving a metadata reader from the block reader by its index
IMetadataReader = IMetadataBlockReader.GetReaderByIndex(0)
#Retrieving and exploring the component infos from the reader
IMetadataReaderInfo = IMetadataReader.GetMetadataHandlerInfo()
print(IMetadataReaderInfo.GetComponentType(), IMetadataReaderInfo.GetCLSID(), IMetadataReaderInfo.GetFriendlyName())
print(IMetadataReaderInfo.GetMetadataFormat(), IMetadataReaderInfo.GetContainerFormats(), IMetadataReaderInfo.GetDeviceManufacturer(),  IMetadataReaderInfo.GetDeviceModels(), IMetadataReaderInfo.DoesRequireFullStream(), IMetadataReaderInfo.DoesSupportPadding(), IMetadataReaderInfo.DoesRequireFixedSize())
print(IMetadataReaderInfo.GetPatterns('jpg'))
#Creating a metadata reader from the component info instance
print(IMetadataReaderInfo.CreateInstance().GetMetadataFormat())

#Metadata reader stream manipulation
#Creating a stream provider from the metadata reader
IStreamProvider = IMetadataReader.GetStreamProvider()
print(IStreamProvider.GetPersistOptions(), IStreamProvider.GetPreferredVendorGUID())
#Retrieving the stream feeding the metadata reader
IMStream = IStreamProvider.GetStream()
#Checking that the stream starts with the right pattern
s = IMStream.Seek()
print(IMetadataReaderInfo.MatchesPattern('jpg', IMStream))
IMetadataReaderInfo.Release()
#Retrieving the length of the metadata segment
print(IMStream.Seek(0, 'end'))
#reading the first four bytes of the metadata segment
IMStream.Seek(s, 'beginning')
print(IMStream.Get(4).tobytes())
#Creating a new metadata reader upon the stream
IMStream.Seek(s, 'beginning')
IMetadataReader2 = IComponentFactory.CreateMetadataReader(IMetadataReader.GetMetadataFormat(), options=IStreamProvider.GetPersistOptions(), istream=IMStream)
print(*(r[2].GetMetadataFormat() for r in IMetadataReader2.GetEnumerator()))
IMetadataReader2.Release()
#Creating an uninitialized metadata reader with the same format
IMetadataReader2 = IComponentFactory.CreateMetadataReader(IMetadataReader.GetMetadataFormat())
#Retrieving the persist stream of this new reader
IPersistStream = IMetadataReader2.GetPersistStream()
print(IPersistStream.GetClassID())
IMStream.Seek(s,'beginning')
#Loading the stream of the first metadata reader in the new reader through the persist stream
IPersistStream.LoadEx(IMStream, options=IStreamProvider.GetPersistOptions())
print(*(r[2].GetMetadataFormat() for r in IMetadataReader2.GetEnumerator()))
#Creating a metadata writer initialized with the metadata reader
IMetadataWriter2 = IComponentFactory.CreateMetadataWriterFromReader(IMetadataReader2)
print(*(r[2].GetMetadataFormat() for r in IMetadataWriter2.GetEnumerator()))
IMetadataReader2.Release()
IMetadataReader.Release()
IMStream.Release()
IStreamProvider.Release()
IPersistStream.Release()
#Retrieving a metadata writer from the block writer by its index
IMetadataWriter = IMetadataBlockWriter.GetWriterByIndex(0)
#Retrieving and exploring the component infos from the writer
IMetadataWriterInfo = IMetadataWriter.GetMetadataHandlerInfo()
print(IMetadataWriterInfo.GetComponentType(), IMetadataWriterInfo.GetCLSID(), IMetadataWriterInfo.GetFriendlyName())
print(IMetadataWriterInfo.GetMetadataFormat(), IMetadataWriterInfo.GetContainerFormats(), IMetadataWriterInfo.GetDeviceManufacturer(),  IMetadataWriterInfo.GetDeviceModels(), IMetadataWriterInfo.DoesRequireFullStream(), IMetadataWriterInfo.DoesSupportPadding(), IMetadataWriterInfo.DoesRequireFixedSize())
print(IMetadataWriterInfo.GetHeader('jpg'))
IMetadataWriterInfo.Release()
#Retrieving the stream of the writer through a stream provider
IStreamProvider = IMetadataWriter.GetStreamProvider()
IMStream = IStreamProvider.GetStream()
#Reading the first four bytes
print(IMStream.Get(4).tobytes())
#Creating an uninitialized metadata writer with the same format
IMetadataWriter2 = IComponentFactory.CreateMetadataWriter(IMetadataWriter.GetMetadataFormat())
#Setting a metadata value by its index from the previous writer
IMetadataWriter2.SetValueByIndex(0, *IMetadataWriter.GetValueWithTypeByIndex(0)[:2], IMetadataWriter.GetValueWithTypeByIndex(0)[2])
#Retrieving the persist stream of the new writer
IPersistStream = IMetadataWriter2.GetPersistStream()
print(IPersistStream.GetClassID())
print(IPersistStream.GetClassID(), IPersistStream.GetSizeMax())
#Saving the content of the new metadata writer to a new in memory stream
IMStream = IStream.CreateInMemory()
IPersistStream.SaveEx(IMStream, options=IStreamProvider.GetPersistOptions())
#Reading the first four bytes
print(IMStream.Seek())
IMStream.Seek(0, 'beginning')
print(IMStream.Get(4).tobytes())
#Releasing interfaces
tuple(map(IUnknown.Release, (IStreamProvider, IPersistStream, IMetadataWriter2, IMetadataWriter, IMetadataQueryWriter, IMetadataBlockWriter, IMetadataQueryReader, IMetadataBlockReader, IBitmapFrameEncode, IEncoderOptions, IEncoder, IStream2, IBitmapFrame, IDecoder)))

#Creating an encoder options property bag in a different thread
def f():
  IWICComponentFactory()
  print('Not initialized for the thread ->', IGetLastError())
  Initialize()
  IComponentFactory = IWICComponentFactory()
  PropertyBag = IComponentFactory.CreateEncoderPropertyBag({'test': 'VT_BSTR', 'test2': 'VT_I4'})
  print(PropertyBag.CountProperties(), PropertyBag.GetPropertyInfo())
  PropertyBag.Write({'test': ('VT_BSTR', 'rr')})
  PropertyBag.SetProperties({'test2':5})
  print(PropertyBag.GetProperties())
  PropertyBag.Release()
  IComponentFactory.Release()
  Uninitialize()
th=threading.Thread(target=f)
th.start()
th.join()

#Editing metadata in a jpeg image without reencoding
p = path + r'\test.jpg'
#Decoding the file
IDecoder = IImagingFactory.CreateDecoderFromFilename(p)
IDecoderInfo = IDecoder.GetDecoderInfo()
IBitmapFrame = IDecoder.GetFrame(0)
#Retrieving the app1 and icc metadata segments
IMetadataBlockReader = IBitmapFrame.GetMetadataBlockReader()
e = IMetadataBlockReader.GetEnumerator()
IMetadataReader1 = next((reader for reader in e if reader.GetMetadataFormat() == 'App1'), None)
e.Reset()
IMetadataReader2 = next((reader for reader in e if reader.GetMetadataFormat() == 'Unknown'), None)
e.Release()
#Creating the jpeg frame decode
IJpegFrameDecode = IBitmapFrame.GetJpegFrameDecode()
#Creating an encoder to a in memory stream
IPStream = IStream.CreateInMemory()
IEncoder = IImagingFactory.CreateEncoder('jpeg')
IEncoder.Initialize(IPStream)
IBitmapFrameEncode, IEncoderOptions = IEncoder.CreateNewFrame()
#Setting the tables, size and pixel format accordingly to the decoded frame
IEncoderOptions.SetProperties({'JpegYCrCbSubsampling': IJpegFrameDecode.GetFrameHeader()['SampleFactors'].name[-3:], 'Luminance': IJpegFrameDecode.GetQuantizationTable(0, 0), 'Chrominance': IJpegFrameDecode.GetQuantizationTable(0, 1), 'JpegLumaAcHuffmanTable': IJpegFrameDecode.GetAcHuffmanTable(0,0), 'JpegLumaDcHuffmanTable': IJpegFrameDecode.GetDcHuffmanTable(0,0), 'JpegChromaAcHuffmanTable': IJpegFrameDecode.GetAcHuffmanTable(0,1), 'JpegChromaDcHuffmanTable': IJpegFrameDecode.GetDcHuffmanTable(0,1), 'SuppressApp0': True})
IBitmapFrameEncode.Initialize(IEncoderOptions)
IBitmapFrameEncode.SetSize(*IBitmapFrame.GetSize())
print(IBitmapFrameEncode.SetPixelFormat(IBitmapFrame.GetPixelFormat()) == IBitmapFrame.GetPixelFormat())
#Creating the jpeg frame encode
IJpegFrameEncode = IBitmapFrameEncode.GetJpegFrameEncode()
#Copying the compressed data from the jpeg frame decode to the jpeg frame encode
IJpegFrameEncode.WriteScan(IJpegFrameDecode.CopyScan(0))
#Encoding in the memory stream
IBitmapFrameEncode.Commit()
IEncoder.Commit()
IPStream.Commit()
l = IPStream.Seek()
#Creating a stream to the new file
p2 = path + r'\test-.jpg'
IStream2 = IImagingFactory.CreateStream()
IStream2.InitializeFromFilename(p2, 'write')
#Writing the jpeg header to the new file
IStream2.Write(IDecoderInfo.GetPatterns()[0]['Pattern'])
IPStream.Seek(IStream2.Seek(), 'beginning')
if IMetadataReader1 is not None:
#Creating a metadata writer from the app1 metadata reader
  IMetadataWriter1 = IComponentFactory.CreateMetadataWriterFromReader(IMetadataReader1)
#Retrieving the ifd metadata writer
  IMetadataWriter11 = next(writer[2] for writer in IMetadataWriter1.GetEnumerator() if writer[2].GetMetadataFormat() == 'Ifd')
#Setting the new metadata values
  IMetadataWriter11.SetValue(('VT_EMPTY', None), ('VT_UI2', 271), ('VT_LPSTR', b'Manufacturer'))
  IMetadataWriter11.SetValue(('VT_EMPTY', None), ('VT_UI2', 315), ('VT_LPSTR', b'Artist'))
#Retrieving the persist stream of the app1 metadata writer
  IMetadataWriterInfo = IMetadataWriter1.GetMetadataHandlerInfo()
  IStreamProvider = IMetadataWriter1.GetStreamProvider()
  IPersistStream = IMetadataWriter1.GetPersistStream()
#Encoding the app1 metadata in a in memory stream
  IMStream = IStream.CreateInMemory()
  IPersistStream.SaveEx(IMStream, options=IStreamProvider.GetPersistOptions())
  m = IMStream.Seek()
#Writing the app1 metadata header to the new file
  h = IMetadataWriterInfo.GetHeader('jpeg')
  IStream2.Write(h['Header'][:h['DataOffset'] - 2])
#Writing the app1 metadata length to the new file
  if h['DataOffset'] >= 2:
    IStream2.Write((m + 2).to_bytes(2, 'big'))
#Copying the encoded metadata to the new file
  IMStream.Seek(0, 'beginning')
  IMStream.CopyTo(IStream2, m)
  tuple(map(IUnknown.Release, (IMetadataWriterInfo, IStreamProvider, IPersistStream, IMStream, IMetadataWriter1, IMetadataWriter11, IMetadataReader1)))
if IMetadataReader2 is not None:
#Creating a metadata writer from the icc metadata reader
  IMetadataWriter2 = IComponentFactory.CreateMetadataWriterFromReader(IMetadataReader2)
#Retrieving the persist stream of the icc metadata writer
  IMetadataWriterInfo = IMetadataWriter2.GetMetadataHandlerInfo()
  IStreamProvider = IMetadataWriter2.GetStreamProvider()
  IPersistStream = IMetadataWriter2.GetPersistStream()
#Encoding the icc metadata in a in memory stream
  IMStream = IStream.CreateInMemory()
  IPersistStream.SaveEx(IMStream, options=IStreamProvider.GetPersistOptions())
  m = IMStream.Seek()
#Writing the app1 metadata header to the new file
  h = IMetadataWriterInfo.GetHeader('jpeg')
  IStream2.Write(h['Header'][:h['DataOffset'] - 2])
#Writing the app1 metadata length to the new file
  if h['DataOffset'] >= 2:
    IStream2.Write((m + 2).to_bytes(2, 'big'))
#Copying the encoded metadata to the new file
  IMStream.Seek(0, 'beginning')
  IMStream.CopyTo(IStream2, m)
  tuple(map(IUnknown.Release, (IMetadataWriterInfo, IStreamProvider, IPersistStream, IMStream,IMetadataWriter2, IMetadataReader2)))
#Copying the encoded original image to the new file
IPStream.CopyTo(IStream2, l - IPStream.Seek())
IStream2.Commit()
#Releasing interfaces
tuple(map(IUnknown.Release, (IStream2, IMetadataWriter2, IMetadataWriter, IJpegFrameEncode, IBitmapFrameEncode, IEncoderOptions, IEncoder, IPStream, IMetadataBlockReader, IJpegFrameDecode, IBitmapFrame, IDecoderInfo, IDecoder)))

#Planar YCbCr format manipulation
#Decoding the file
p = path + r'\test.jpg'
IDecoder = IImagingFactory.CreateDecoderFromFilename(p, metadata_option='onload')
IBitmapFrame = IDecoder.GetFrame(0)
#Creating the planar data provider
IPlanarBitmapSourceTransform = IBitmapFrame.GetPlanarBitmapSourceTransform()
#Checking if 3 planes mode is supported
r, w, h, pds = IPlanarBitmapSourceTransform.DoesSupportTransform(100, 100, 'rotate0', 'preservesubsampling', ('8bppY', '8bppCb', '8bppCr'))
print(r, w, h, pds)
#Retrieving the 3 planes
bs = tuple(bytearray(pd['Width'] * pd['Height']) for pd in pds)
IPlanarBitmapSourceTransform.CopyPixels(None, w, h, 'rotate0', 'preservesubsampling', ({'Format': '8bppY', 'pbBuffer': bs[0], 'cbStride': pds[0]['Width']}, WICBITMAPPLANE('8bppCb', ctypes.cast(ctypes.pointer((ctypes.c_char * len(bs[1])).from_buffer(bs[1])), ctypes.c_void_p), pds[1]['Width'], len(bs[1])), ('8bppCr', bs[2], pds[2]['Width'])))
print(*(len(b) for b in bs))
#Checking if 2 planes mode is supported
r, w, h, pds = IPlanarBitmapSourceTransform.DoesSupportTransform(100, 100, 'rotate0', 'preservesubsampling', ('8bppY', '16bppCbCr'))
print(r, w, h, pds)
#Retrieving the 2 planes
bs2 = tuple(bytearray(pd['Width'] * pd['Height'] * (IImagingFactory.CreateComponentInfo(pd['Format']).GetBitsPerPixel() // 8)) for pd in pds)
IPlanarBitmapSourceTransform.CopyPixels(None, w, h, 'rotate0', 'preservesubsampling', tuple((pd['Format'], b, pd['Width'] * (IImagingFactory.CreateComponentInfo(pd['Format']).GetBitsPerPixel() // 8)) for pd, b in zip(pds, bs2)))
print(*(len(b) for b in bs2))
#Checking that the planes of the two modes matches
print(bs[0]==bs2[0], bs[1]==bs2[1][::2], bs[2]==bs2[1][1::2])
del bs
#Creating the planar format converter
IFormatConverter = IImagingFactory.CreateFormatConverter()
IPlanarFormatConverter = IFormatConverter.GetPlanarFormatConverter()
IFormatConverter.Release()
#Checking if conversion to BGR is supported
print(IPlanarFormatConverter.CanConvert(tuple(pd['Format'] for pd in pds), '24bppBGR'))
#Creating the two planes bitmaps
IBitmaps = tuple(IImagingFactory.CreateBitmap(pd['Width'], pd['Height'], pd['Format']) for pd in pds)
#Writing data to the planes bitmaps
IBitmapLocks = tuple(IBitmap.Lock(None, 'write') for IBitmap in IBitmaps)
IPlanarBitmapSourceTransform.CopyPixels(None, w, h, 'rotate0', 'preservesubsampling', IBitmapLocks)
tuple(map(IUnknown.Release, IBitmapLocks))
#Initializing the planar format converter
IPlanarFormatConverter.Initialize(IBitmaps, '24bppBGR')
#Checking the format of the converted bitmap
print(IPlanarFormatConverter.GetSize(), IPlanarFormatConverter.GetPixelFormat())
IPlanarFormatConverter.Release()
IPlanarBitmapSourceTransform.Release()
#Creating and initializing an encoder
p2 = path + r'\test-.jpg'
IStream2 = IStream.CreateOnFile(p2, 'write')
IEncoder = IImagingFactory.CreateEncoder('jpeg')
IEncoder.Initialize(IStream2)
IBitmapFrameEncode, IEncoderOptions = IEncoder.CreateNewFrame()
IEncoderOptions.JpegYCrCbSubsampling = IBitmapFrame.GetJpegFrameDecode().GetFrameHeader()['SampleFactors'].name[-3:]
IBitmapFrameEncode.Initialize(IEncoderOptions)
#Retrieving a planar frame encoder
IPlanarBitmapFrameEncode = IBitmapFrameEncode.GetPlanarBitmapFrameEncode()
#Writing the planes bitmaps to the planar frame
IPlanarBitmapFrameEncode.WriteSource(IBitmaps)
#Finalizing the encoding
IBitmapFrameEncode.Commit()
IEncoder.Commit()
tuple(map(IUnknown.Release, (IPlanarBitmapFrameEncode, IBitmapFrameEncode, IEncoderOptions, IEncoder, IStream2)))
#Creating and initializing an encoder
IStream2 = IStream.CreateOnFile(p2, 'write')
IEncoder = IImagingFactory.CreateEncoder('jpeg')
IEncoder.Initialize(IStream2)
IBitmapFrameEncode, IEncoderOptions = IEncoder.CreateNewFrame()
IEncoderOptions.JpegYCrCbSubsampling = IBitmapFrame.GetJpegFrameDecode().GetFrameHeader()['SampleFactors'].name[-3:]
IBitmapFrameEncode.Initialize(IEncoderOptions)
IBitmapFrameEncode.SetSize(w, h * 2)
IBitmapFrameEncode.SetPixelFormat(IBitmapFrame .GetPixelFormat())
#Retrieving a planar frame encoder
IPlanarBitmapFrameEncode = IBitmapFrameEncode.GetPlanarBitmapFrameEncode()
#Writing the pixels from the previous buffers in the planar frame
IPlanarBitmapFrameEncode.WritePixels(h, tuple((pd['Format'], b, pd['Width'] * (IImagingFactory.CreateComponentInfo(pd['Format']).GetBitsPerPixel() // 8)) for pd, b in zip(pds, bs2)))
del bs2
#Writing the pixels from the plane bitmaps in the planar frame
IBitmapLocks = tuple(IBitmap.Lock(None, 'read') for IBitmap in IBitmaps)
IPlanarBitmapFrameEncode.WritePixels(h, IBitmapLocks)
tuple(map(IUnknown.Release, (*IBitmapLocks, *IBitmaps)))
#Finalizing the encoding
IBitmapFrameEncode.Commit()
IEncoder.Commit()
tuple(map(IUnknown.Release, (IPlanarBitmapFrameEncode, IBitmapFrameEncode, IEncoderOptions, IEncoder, IStream2)))
tuple(map(IUnknown.Release, (IBitmapFrame, IDecoder)))

#Releasing the factory interfaces
IImagingFactory.Release()
IComponentFactory.Release()

#Retrieving Media Photo Library
ILibrary = IWMPCore().GetPhotos()
att = ('Title', 'RecordingTimeDate', 'Width', 'Height', 'SourceURL')
print(tuple(dict(zip((att), inf)) for inf in ILibrary.GetInfos(*att)))
#Retrieving Media Photo Library by query on height and width greater than 1920x1080 or 1080x1920 and descending sort on recording date
ILibrary2 = ILibrary.factory.factory.GetPhotosByQuery(((('Height', 'greaterthan', '1080'), ('width', 'greaterthan', '1920')), (('Height', 'greaterthan', '1920'), ('width', 'greaterthan', '1080'))), 'recordingtime', False)
print(tuple(dict(zip((att), inf)) for inf in ILibrary2.GetInfos(*att)))
#Retrieving first photo and printing its title and recording time in local format
import locale
locale.setlocale(locale.LC_TIME, '')
IPhoto = ILibrary.GetItem(0)
if IPhoto:
  print(IPhoto.Title, IPhoto.GetItemInfoWithTypeByType('RecordingTime'))
#Release the interfaces
  IPhoto.Release()
del ILibrary2
del ILibrary

#Creating a D3D11 device and getting the underlying DXGI device
D3D11Device = ID3D11Device()
DXGIDevice = D3D11Device.GetDXGIDevice()
#Creating a D2D1 factory
D2D1Factory = ID2D1Factory()
#Creating a D2D1 device
D2D1Device = D2D1Factory.CreateDevice(DXGIDevice)
print(D2D1Device, D2D1Device.GetMaximumTextureMemory())
#Creating a D2D1 device context from the D2D1 device
D2D1DeviceContext = D2D1Device.CreateDeviceContext()
print(D2D1DeviceContext.GetDevice().pI, D2D1Device.pI)
#Retrieving and changing the rendering controls
print(rc := D2D1DeviceContext.GetRenderingControls())
D2D1DeviceContext.SetRenderingControls(('8BPC_UNORM', (2048, 2048)))
print(D2D1DeviceContext.GetRenderingControls())
D2D1DeviceContext.SetRenderingControls(rc)
#Retrieving and changing the primitive blend
print(D2D1DeviceContext.GetPrimitiveBlend())
D2D1DeviceContext.SetPrimitiveBlend('Max')
print(D2D1DeviceContext.GetPrimitiveBlend())
D2D1DeviceContext.SetPrimitiveBlend()
#Retrieving all supported and unsupported DXGI formats
print(sorted(((f, D2D1DeviceContext.IsDxgiFormatSupported(f)) for f in DXGIFormat), key=(lambda t: t[1]), reverse=True))
#Creating D2D1 color contexts from type, file, WIC color context
D2D1ColorContext = D2D1DeviceContext.CreateColorContext('sRGB')
print(D2D1ColorContext.GetColorSpace(), len(D2D1ColorContext.GetProfileBytes()))
D2D1ColorContext2 = D2D1DeviceContext.CreateColorContext('Custom', D2D1ColorContext.GetProfileBytes())
print(D2D1ColorContext2.GetColorSpace(), len(D2D1ColorContext2.GetProfileBytes()))
D2D1ColorContext2 = D2D1DeviceContext.CreateColorContextFromFilename(path + r'\sDCIP3.col')
print(D2D1ColorContext2.GetColorSpace(), len(D2D1ColorContext2.GetProfileBytes()))
IImagingFactory = IWICImagingFactory()
IColorContext = IImagingFactory.CreateColorContext()
IColorContext.InitializeFromExifColorSpace('AdobeRGB')
D2D1ColorContext2 = D2D1DeviceContext.CreateColorContextFromWicColorContext(IColorContext)
IColorContext.Release()
print(D2D1ColorContext2.GetColorSpace(), len(D2D1ColorContext2.GetProfileBytes()))
D2D1ColorContext2.Release()
#Creating a D2D1 bitmap for rendering
D2D1Bitmap = D2D1DeviceContext.CreateBitmap(320, 200, {'pixelFormat': ('B8G8R8A8_UNORM', 'premultiplied'), 'bitmapOptions':'target | cannotdraw', 'colorContext': D2D1ColorContext})
#Other way to do the same
# D2D1Bitmap = D2D1DeviceContext.CreateTargetBitmap(width=320, height=200, format='B8G8R8A8_UNORM', alpha_mode='premultiplied', color_context=D2D1ColorContext)
print(D2D1Bitmap.GetSize(), D2D1Bitmap.GetPixelSize(), D2D1Bitmap.GetPixelFormat(), D2D1Bitmap.GetDpi(), D2D1Bitmap.GetColorContext(), D2D1Bitmap.GetOptions())
#Retrieving the underlying DXGI surface of the D2D1 bitmap
DXGISurface = D2D1Bitmap.GetSurface()
print(DXGISurface.GetDevice().pI, DXGIDevice.pI)
print(DXGISurface.GetDesc())
#Creating a D2D1 bitmap from the DXGI surface
D2D1Bitmap2 = D2D1DeviceContext.CreateBitmapFromDxgiSurface(DXGISurface)
#Other way to do the same
# D2D1Bitmap2 = D2D1DeviceContext.CreateTargetBitmap(DXGISurface)
print(D2D1Bitmap2.GetSize(), D2D1Bitmap2.GetPixelSize(), D2D1Bitmap2.GetPixelFormat(), D2D1Bitmap2.GetDpi(), D2D1Bitmap2.GetColorContext(), D2D1Bitmap2.GetOptions())
D2D1Bitmap2.Release()
#Creating two D2D1 bitmaps from a WIC Bitmap after conversion to the right pixel format for CPU reading and general purpose
IDecoder = IImagingFactory.CreateDecoderFromFilename(path + r'\test-p3.jpg', metadata_option='onload')
IBitmapFrame = IDecoder.GetFrame(0)
IFormatConverter = IImagingFactory.CreateFormatConverter()
IFormatConverter.Initialize(IBitmapFrame, '32bppPBGRA')
D2D1Bitmap2 = D2D1DeviceContext.CreateBitmapFromWICBitmap(IFormatConverter, {'pixelFormat': ('B8G8R8A8_UNORM', 'premultiplied'), 'bitmapOptions':'cpuread | cannotdraw', 'colorContext': D2D1ColorContext})
#Other way to do the same
# D2D1Bitmap2 = D2D1DeviceContext.CreateCPUReadableBitmap(source=IFormatConverter, format='B8G8R8A8_UNORM', alpha_mode='premultiplied', color_context=D2D1ColorContext)
D2D1Bitmap3 = D2D1DeviceContext.CreateBitmapFromWICBitmap(IFormatConverter, {'pixelFormat': ('B8G8R8A8_UNORM', 'premultiplied'), 'colorContext': D2D1ColorContext})
#Other way to do the same
# D2D1Bitmap3 = D2D1DeviceContext.CreateDefaultBitmap(source=IFormatConverter, color_context= D2D1ColorContext)
print(D2D1Bitmap2.GetSize(), D2D1Bitmap2.GetPixelSize(), D2D1Bitmap2.GetPixelFormat(), D2D1Bitmap2.GetDpi(), D2D1Bitmap2.GetColorContext(), D2D1Bitmap2.GetOptions())
#Retrieving the underlying DXGI surface of the first D2D1 bitmap
DXGISurface2 = D2D1Bitmap2.GetSurface()
print(DXGISurface2.GetDesc())
#Mapping the DXGI Surface for reading
print(DXGISurface2.Map('read'))
#Unmmapping the DXGI Surface
DXGISurface2.Unmap()
#Mapping the D2D1 bitmap for reading
print(D2D1Bitmap2.Map('read'))
#Unmapping the D2D1 bitmap
D2D1Bitmap2.Unmap()
#Copying a part of the first D2D1 bitmap in the second one
D2D1Bitmap2.CopyFromBitmap(D2D1Bitmap, (5,5), (0,0,10,10))
#Mapping the D2D1 bitmap for reading
print(D2D1Bitmap2.Map('read')[5][19:61])
#Unmapping the D2D1 bitmap
D2D1Bitmap2.Unmap()
D2D1Bitmap2.Release()
DXGISurface2.Release()
#Setting the D2D1 bitmap created for rendering as the target of the D2D1 device context
D2D1DeviceContext.SetTarget(D2D1Bitmap)
#Starting to draw
D2D1DeviceContext.BeginDraw()
#Clearing
D2D1DeviceContext.Clear((0.5, 0.5, 0.5, 1))
#Finishing drawing
D2D1DeviceContext.EndDraw()
#creating a D2D1 bitmap for CPU reading
D2D1Bitmap2 = D2D1DeviceContext.CreateBitmap(320, 200, {'pixelFormat': ('B8G8R8A8_UNORM', 'premultiplied'), 'bitmapOptions':'cpuread | cannotdraw', 'colorContext': D2D1ColorContext})
#Other way to do the same
# D2D1Bitmap2 = D2D1DeviceContext.CreateCPUReadableBitmap(width=320, height=200, color_context=D2D1ColorContext)
#Copying the target of the D2D1 device context in this D2D1 bitmap
D2D1Bitmap2.CopyFromRenderTarget(D2D1DeviceContext)
#Mapping the D2D1 bitmap for reading then unmapping it
print(D2D1Bitmap2.Map('read')[0][0:12])
D2D1Bitmap2.Unmap()
#Copying data to the D2D1 bitmap created for rendering
D2D1Bitmap.CopyFromMemory(b'\x01' * 320 * 4 * 2, 320 * 4, (0, 0, 320, 2))
#Copying the D2D1 bitmap created for rendering to the D2D1 bitmap created for CPU reading
D2D1Bitmap2.CopyFromBitmap(D2D1Bitmap)
#Mapping the D2D1 bitmap for reading then unmapping it
print(D2D1Bitmap2.Map('read')[1][0:320*4:4])
D2D1Bitmap2.Unmap()
#Creating and attaching a D2D1 command list
D2D1CommandList = D2D1DeviceContext.CreateCommandList()
D2D1DeviceContext.SetTarget(D2D1CommandList)
#Starting to draw again
D2D1DeviceContext.BeginDraw()
#Drawing the D2D1 bitmap created from the WIC bitmap
D2D1DeviceContext.DrawBitmap(D2D1Bitmap3, (0, 0, 320, 200), 1, 'HighQualityCubic', (0, 0, 1920, 1080))
#Creating a solid color red D2D1 brush
D2D1ColorBrush = D2D1DeviceContext.CreateBrush((1.0, 0.0, 0.0, 0.8), opacity=0.5,transform=ID2D1Factory.MakeTranslationMatrix(5,9))
print(D2D1ColorBrush.GetColor(), D2D1ColorBrush.GetOpacity(), D2D1ColorBrush.GetTransform()[:])
#Creating a D2D1 collection of three gradient stops (R->G->B)
D2D1GradientStopCollection = D2D1DeviceContext.CreateGradientStopCollection(((0,(1,0,0,1)),(0.5,(0,1,0,1)),(1,(0,0,1,1))), buffer_precision='8bpc_unorm_srgb')
print(D2D1GradientStopCollection.GetExtendMode(), D2D1GradientStopCollection.GetColorInterpolationGamma(), D2D1GradientStopCollection.GetPreInterpolationSpace(), D2D1GradientStopCollection.GetPostInterpolationSpace(),D2D1GradientStopCollection.GetBufferPrecision(),D2D1GradientStopCollection.GetGradientStopCount(), D2D1GradientStopCollection.GetGradientStops())
#Creating a linear gradient D2D1 brush upon these gradient stops
D2D1LinearGradientBrush = D2D1DeviceContext.CreateBrush(D2D1GradientStopCollection, gradient_start_point=(0,0), gradient_end_point=(120,60), opacity=1,transform=ID2D1Factory.MakeTranslationMatrix(200,20), gradient_color_interpolation_mode=0)
print(D2D1LinearGradientBrush.GetStartPoint(), D2D1LinearGradientBrush.GetEndPoint())
#Creating a radial gradient D2D1 brush (W->B) and retrieving its gradient stops
D2D1RadialGradientBrush = D2D1DeviceContext.CreateBrush(((1.0, (0.0, 0.0, 0.0, 1.0)), (0.0, (1.0, 1.0, 1.0, 1.0))), gradient_center=(60,60), gradient_origin_offset=(-30,-30), gradient_radius=(80,80), opacity=1,transform=ID2D1Factory.MakeTranslationMatrix(190,100))
print(D2D1RadialGradientBrush.GetCenter(), D2D1RadialGradientBrush.GetGradientOriginOffset(), D2D1RadialGradientBrush.GetRadius())
D2D1GradientStopCollection = D2D1RadialGradientBrush.GetGradientStopCollection()
print(D2D1GradientStopCollection.GetExtendMode(), D2D1GradientStopCollection.GetColorInterpolationGamma(), D2D1GradientStopCollection.GetPreInterpolationSpace(), D2D1GradientStopCollection.GetPostInterpolationSpace(),D2D1GradientStopCollection.GetBufferPrecision(),D2D1GradientStopCollection.GetGradientStopCount(), D2D1GradientStopCollection.GetGradientStops(), D2D1GradientStopCollection.GetColorInterpolationMode())
#Creating a rescaled D2D1 bitmap from the WIC bitmap
IScaler = IImagingFactory.CreateBitmapScaler()
IScaler.Initialize(IFormatConverter, 80, 45, 'HighQualityCubic')
D2D1BitmapB = D2D1DeviceContext.CreateBitmapFromWICBitmap(IScaler, {'pixelFormat': ('B8G8R8A8_UNORM', 'premultiplied'), 'colorContext': D2D1ColorContext})
#Creating a bitmap D2D1 brush from the rescaled D2D1 bitmap
D2D1BitmapBrush = D2D1DeviceContext.CreateBrush(D2D1BitmapB, extend_mode=('wrap', 'wrap'), bitmap_interpolation_mode='HighQualityCubic', opacity=1, transform=ID2D1Factory.MakeRotateMatrix(90, (0, 0)))
print(D2D1BitmapBrush.GetBitmap(), D2D1BitmapBrush.GetExtendModeX(), D2D1BitmapBrush.GetExtendModeY())
#Creating a custom D2D1 stroke style
D2D1StrokeStyle = D2D1DeviceContext.CreateStrokeStyle('square', 'triangle', 'round', 'MiterOrBevel', 1, 'custom', 0, 'fixed', (2.0, 2.0, 0.5, 2.0))
print(D2D1StrokeStyle.GetStartCap(), D2D1StrokeStyle.GetEndCap(), D2D1StrokeStyle.GetDashCap(), D2D1StrokeStyle.GetMiterLimit(), D2D1StrokeStyle.GetLineJoin(), D2D1StrokeStyle.GetDashOffset(), D2D1StrokeStyle.GetDashStyle(), D2D1StrokeStyle.GetStrokeTransformType())
print(D2D1StrokeStyle.GetDashesCount(), D2D1StrokeStyle.GetDashes())
#Drawing a line with the bitmap brush and this stroke style
D2D1DeviceContext.DrawLine((20, 20), (300, 20), D2D1BitmapBrush, 40, D2D1StrokeStyle)
#Creating a solid D2D1 stroke style
D2D1StrokeStyle = D2D1DeviceContext.CreateStrokeStyle('square', 'triangle', 'round', 'MiterOrBevel', 1, 'solid', 0, 'fixed')
#Drawing a rectangle with the color brush and the stroke style, then filling it with the bitmap brush
D2D1DeviceContext.DrawRectangle((40, 10, 155, 150), D2D1ColorBrush, 20, D2D1StrokeStyle)
D2D1BitmapBrush.SetOpacity(0.5)
D2D1DeviceContext.FillRectangle((40, 10, 155, 150), D2D1BitmapBrush)
#Drawing an ellipse with the linear gradient brush, then filling it with the bitmap brush
D2D1BitmapBrush.SetOpacity(1)
D2D1DeviceContext.DrawEllipse(((260, 50), 50, 20), D2D1LinearGradientBrush, 20)
D2D1BitmapBrush.SetOpacity(0.5)
D2D1DeviceContext.FillEllipse(((260, 50), 50, 20), D2D1BitmapBrush)
#Creating a bitmap D2D1 brush from the rescaled D2D1 bitmap vertically mirrored (as rotated)
D2D1BitmapBrush = D2D1DeviceContext.CreateBrush(D2D1BitmapB, extend_mode=('mirror', 'wrap'), bitmap_interpolation_mode='HighQualityCubic', opacity=1, transform=ID2D1Factory.MakeRotateMatrix(90, (0, 0)))
#Drawing a rounded rectangle with the radial gradient brush after having filled it with the bitmap brush
D2D1BitmapBrush.SetOpacity(0.5)
D2D1DeviceContext.FillRoundedRectangle(((200, 110, 300, 200), 50, 20), D2D1BitmapBrush)
D2D1BitmapBrush.SetOpacity(1)
D2D1DeviceContext.DrawRoundedRectangle(((200, 110, 300, 200), 50, 20), D2D1RadialGradientBrush, 20)
#Listing effects
for e in D2D1Factory.GetRegisteredEffects():
  print(e, D2D1Factory.GetEffectProperties(e)['Description']())
#Creating a brightness effect and handling its properties
D2D1Effect = D2D1DeviceContext.CreateEffect('Brightness')
print(D2D1Effect.GetCustom())
print(D2D1Effect.GetSystem())
print(D2D1Effect['WhitePoint'].Get())
print(D2D1Effect['WhitePoint'].GetSubs().GetAll())
print(D2D1Effect['Precision']['Fields']())
print(p := D2D1Effect['Precision']())
D2D1Effect['Precision']('Uint8')
print(D2D1Effect['Precision']())
D2D1Effect['Precision'](p)
print(D2D1Effect['Precision'].Get())
D2D1Effect['WhitePoint']((0.9, 1))
D2D1Effect['BlackPoint']((0.1, 0))
D2D1Effect.SetInput(0, D2D1Bitmap3)
print(D2D1Effect.GetInputs())
#Creating and chaining a scale effect to adjust the image to the target size
D2D1Effect2 = D2D1DeviceContext.CreateEffect('Scale')
D2D1Effect2['Scale']((320/1920, 200/1080))
D2D1Effect2['BorderMode']('Hard')
D2D1Effect2['InterpolationMode']('Anisotropic')
D2D1Effect2.SetInputEffect(0, D2D1Effect)
#Creating and chaining an edge detection effect
D2D1Effect3 = D2D1DeviceContext.CreateEffect('EdgeDetection')
D2D1Effect3.SetInputEffect(0, D2D1Effect2)
#Drawing the image
D2D1DeviceContext.DrawImage(D2D1Effect3, composite_mode='plus')
#Finishing drawing
D2D1DeviceContext.EndDraw()
#Closing the command list
D2D1CommandList.Close()
#Setting the D2D1 bitmap created for rendering as the target of the D2D1 device context
D2D1DeviceContext.SetTarget(D2D1Bitmap)
#Drawing the command list
D2D1DeviceContext.BeginDraw()
D2D1DeviceContext.DrawImage(D2D1CommandList)
D2D1DeviceContext.EndDraw()
#Copying the target of the D2D1 device context in this D2D1 bitmap
D2D1Bitmap2.CopyFromRenderTarget(D2D1DeviceContext)
#Writing the D2D1 bitmap to a WIC encoder frame and saving the jpg to a file
IImageEncoder = IImagingFactory.CreateImageEncoder(D2D1Device)
Stream = IStream.CreateOnFile(path + r'\test_d.jpg', 'write')
IEncoder = IImagingFactory.CreateEncoder('jpeg')
IEncoder.Initialize(Stream)
IBitmapFrameEncode, IEncoderOptions = IEncoder.CreateNewFrame()
IBitmapFrameEncode.Initialize(IEncoderOptions)
IColorContext = IImagingFactory.CreateColorContext()
IColorContext.InitializeFromExifColorSpace('srgb')
IBitmapFrameEncode.SetColorContexts((IColorContext,))
IBitmapFrameEncode.SetSize(320,200)
IBitmapFrameEncode.SetPixelFormat('24bppBGR')
IImageEncoder.WriteFrame(D2D1Bitmap2, IBitmapFrameEncode)
IBitmapFrameEncode.Commit()
IEncoder.Commit()
tuple(map(IUnknown.Release, (D2D1Bitmap3, IEncoder, IBitmapFrameEncode, IEncoderOptions, Stream, IImageEncoder, IColorContext, D2D1StrokeStyle, D2D1ColorBrush, D2D1LinearGradientBrush, D2D1GradientStopCollection, D2D1RadialGradientBrush, D2D1BitmapBrush, D2D1Effect, D2D1Effect2, D2D1Effect3, D2D1BitmapB, IScaler, D2D1CommandList)))
D2D1Device.ClearResources()

#Creating a software D2D1 device
D3D11Device2 = ID3D11Device('Software')
#Creating a D3D11 2D texture for rendering and retrieving the underlying DXGI surface
D3D11Texture2D = D3D11Device2.CreateTexture2D((320, 200, 1, 1, 'B8G8R8A8_UNORM', (1, 0), 0, 'RenderTarget', 0, 0))
print(D3D11Texture2D.GetDesc())
DXGISurface2 = D3D11Texture2D.GetSurface()
#Shorter way to do the same
# DXGISurface2 = D3D11Device2.CreateTargetDXGISurface(320, 200, 'B8G8R8A8_UNORM')
print(DXGISurface2.GetDesc())
#Creating a D2D1 render target from the DXGI surface
D2D1RenderTarget = D2D1Factory.CreateDxgiSurfaceRenderTarget(DXGISurface2, {'pixelFormat': ('B8G8R8A8_UNORM', 'premultiplied')})
#Other way to do the same
#D2D1RenderTarget = D2D1Factory.CreateRenderTarget(DXGISurface2, format='B8G8R8A8_UNORM', alpha_mode='premultiplied')
#Shorter way to do the same
# DXGISurface2, D2D1RenderTarget = D2D1Factory.CreateSurfaceAndRenderTarget(320, 200, 'B8G8R8A8_UNORM', 'premultiplied')
print(D2D1RenderTarget.GetSize(), D2D1RenderTarget.GetPixelSize(), D2D1RenderTarget.GetPixelFormat(), D2D1RenderTarget.GetDpi(), D2D1RenderTarget.GetAntialiasMode(), D2D1RenderTarget.GetMaximumBitmapSize())
print(D2D1RenderTarget.GetDeviceContext().GetTarget())
#Starting to draw
D2D1RenderTarget.BeginDraw()
#Setting a rotation matrix
D2D1RenderTarget.SetTransform(ID2D1Factory.MakeRotateMatrix(90, (160, 100)))
print(D2D1RenderTarget.GetTransform()[:])
#Matrix operations
print(ID2D1Factory.MakeTranslationMatrix(-160, -100) @ ID2D1Factory.MakeRotateMatrix(90, (0, 0)) @ ID2D1Factory.MakeTranslationMatrix(160, 100) == ID2D1Factory.MakeRotateMatrix(90, (160, 100)))
print(ID2D1Factory.MakeRotateMatrix(90, (160, 100)) @ ~ID2D1Factory.MakeRotateMatrix(90, (160, 100)) == ID2D1Factory.MakeIdentityMatrix())
#Clearing
D2D1RenderTarget.Clear((1, 0, 0, 1))
#Drawing the WIC bitmap
D2D1Bitmap3 = D2D1RenderTarget.CreateBitmapFromWICBitmap(IFormatConverter, {'pixelFormat': ('B8G8R8A8_UNORM', 'premultiplied')})
D2D1RenderTarget.DrawBitmap(D2D1Bitmap3, (80, 55, 240, 145), 0.5, 'Linear', (0, 0, 1920, 1080))
#Creating a WIC bitmap and locking it for reading and writing
IBitmapCache = IImagingFactory.CreateBitmapFromSource(IFormatConverter, 'onload')
IBitmapLock = IBitmapCache.Lock((0, 0, 1920, 1080), 'readwrite')
#Creating a D2D1 shared bitmap from the WIC locked bitmap
D2D1Bitmap4 = D2D1RenderTarget.CreateSharedBitmap(IBitmapLock, {'pixelFormat': ('B8G8R8A8_UNORM', 'premultiplied')})
#Other way to do the same
# D2D1Bitmap4 = D2D1RenderTarget.CreateDefaultBitmap(IBitmapLock)
D2D1RenderTarget.EndDraw()
#Finishing drawing and copying the target to the D2D1 shared bitmap
D2D1Bitmap4.CopyFromRenderTarget(D2D1RenderTarget, (115, 20))
tuple(map(IUnknown.Release, (D2D1Bitmap3, D2D1Bitmap4, IBitmapLock, D2D1RenderTarget, DXGISurface2, IImagingFactory)))
D2D1RenderTarget.Release()
#Creating a D2D1 render target from the WIC bitmap
D2D1RenderTarget = D2D1Factory.CreateWicBitmapRenderTarget(IBitmapCache, {'type': 'software', 'pixelFormat': ('B8G8R8A8_UNORM', 'premultiplied')})
#Other way to do the same
#D2D1RenderTarget = D2D1Factory.CreateRenderTarget(IBitmapCache, format='B8G8R8A8_UNORM', alpha_mode='premultiplied')
#Starting to draw
D2D1RenderTarget.BeginDraw()
#Creating a D2D1 bitmap from the converted WIC bitmap
D2D1Bitmap3 = D2D1RenderTarget.CreateBitmapFromWICBitmap(IFormatConverter, {'pixelFormat': ('B8G8R8A8_UNORM', 'premultiplied')})
#Drawing this D2D1 bitmap
D2D1RenderTarget.DrawBitmap(D2D1Bitmap3, (0, 0, 375, 200), 0.2, 'Linear', (210, 140, 1710, 940))
#Creating a D2D1 bitmap initialized with data
D2D1Bitmap4 = D2D1RenderTarget.CreateBitmap(10, 10, {'pixelFormat': ('B8G8R8A8_UNORM', 'premultiplied')}, b'\xff\x00\xff\xff' * 100, 40)
#Other way to do the same
# D2D1Bitmap4 = D2D1RenderTarget.CreateDefaultBitmap(width=10, height=10, source=b'\xff\x00\xff\xff' * 100, source_pitch=40)
#Drawing this D2D1 bitmap
D2D1RenderTarget.DrawBitmap(D2D1Bitmap4, (1820, 980, 1920, 1080), 1, 'Linear', (0, 0, 10, 10))
#Finishing drawing
D2D1RenderTarget.EndDraw()
tuple(map(IUnknown.Release, (D2D1Bitmap4, D2D1Bitmap3, IFormatConverter, IBitmapFrame, IDecoder, D2D1RenderTarget)))

#Creating a window
user32 = ctypes.WinDLL('user32',  use_last_error=True)
WNDPROC = ctypes.WINFUNCTYPE(wintypes.INT, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)
class WNDCLASSEXW(ctypes.Structure):
  _fields_ = [('cbSize', wintypes.UINT), ('style', wintypes.UINT), ('lpfnWndProc', WNDPROC), ('cbClsExtra', wintypes.INT),  ('cbWndExtra', wintypes.INT), ('hInstance', wintypes.HANDLE),  ('hIcon', wintypes.HANDLE), ('hCursor', wintypes.HANDLE), ('hBrush', wintypes.HANDLE), ('lpszMenuName', wintypes.LPCWSTR), ('lpszClassName', wintypes.LPCWSTR), ('hIconSm', wintypes.HANDLE)]
hInst = kernel32.GetModuleHandleW(wintypes.LPCWSTR(0))
wclassName = 'WICPytest'
wname = 'WICPy test'
wndClass = WNDCLASSEXW(ctypes.sizeof(WNDCLASSEXW), 0, WNDPROC(('DefWindowProcW', user32)), 0,  0, hInst, 0, 0, 0, 0, wintypes.LPCWSTR(wclassName), 0)
regRes = user32.RegisterClassExW(ctypes.byref(wndClass))
hwnd = user32.CreateWindowExW(wintypes.DWORD(0), wintypes.LPCWSTR(wclassName), wintypes.LPCWSTR(wname), wintypes.DWORD(0x10C80000), wintypes.INT(100), wintypes.INT(100), wintypes.INT(800), wintypes.INT(450), wintypes.HWND(0), wintypes.HANDLE(0), hInst, wintypes.LPVOID(0))
#Creating a D2D1 render target to this window
D2D1RenderTarget = D2D1Factory.CreateHwndRenderTarget({'pixelFormat': ('B8G8R8A8_UNORM', 'premultiplied')}, (hwnd, (1920, 1080), 'Immediately | RetainContents'))
#Other way to do the same
#D2D1RenderTarget = D2D1Factory.CreateRenderTarget(hwnd, format='B8G8R8A8_UNORM', alpha_mode='premultiplied', width=1920, height=1080, present_options='Immediately | RetainContents')
#Creating a D2D1 bitmap from the WIC bitmap
D2D1Bitmap4 = D2D1RenderTarget.CreateBitmapFromWICBitmap(IBitmapCache, {'pixelFormat': ('B8G8R8A8_UNORM', 'premultiplied')})
# D2D1Bitmap4 = D2D1RenderTarget.CreateDefaultBitmap(IBitmapCache)
print(hwnd, D2D1RenderTarget.GetHwnd())
#Drawing this bitmap in the window
D2D1RenderTarget.BeginDraw()
D2D1RenderTarget.Clear((0,0,0.2,1))
D2D1RenderTarget.DrawBitmap(D2D1Bitmap4)
D2D1RenderTarget.EndDraw()
D2D1Bitmap4.Release()
#Managing the message queue until the window is closed
print('Waiting for the closure of the pop-up window...')
msg = wintypes.MSG()
lpMsg = ctypes.pointer(msg)
while user32.GetMessageW(lpMsg, hwnd, 0, 0) > 0:
  user32.TranslateMessage(lpMsg)
  user32.DispatchMessageW(lpMsg)
D2D1RenderTarget.Release()

#Creating a window
def PyWndProcedure(hWnd, Msg, wParam, lParam):
  if Msg == 5 and 'DXGISwapChain' in globals():
    h, l = divmod(lParam, 65536)
    print(l, h, DXGISwapChain.ResizeBuffers(), DXGISwapChain.GetDesc())
    D2D1Bitmap3 = D2D1DeviceContext.CreateTargetBitmap(DXGISwapChain.GetSurface())
    D2D1DeviceContext.SetTarget(D2D1Bitmap3)
    D2D1DeviceContext.BeginDraw()
    D2D1DeviceContext.Clear((0,0.5,0,1))
    r = min((l / 1920, h / 1080))
    D2D1DeviceContext.DrawBitmap(D2D1Bitmap4, (0, 0, 1920 * r, 1080 * r), 1, 'HighQualityCubic', (0, 0, 1920, 1080))
    D2D1DeviceContext.EndDraw()
    D2D1DeviceContext.SetTarget()
    D2D1Bitmap3.Release()
    DXGISwapChain.Present()
  elif Msg == 16:
    user32.PostMessageW(hWnd, Msg, wParam, lParam)
    return 0
  return user32.DefWindowProcW(wintypes.HWND(hWnd), wintypes.UINT(Msg), wintypes.WPARAM(wParam), wintypes.LPARAM(lParam))
wname = 'WICPy test resizable'
wclassName = 'WICPytest2'
wndClass2 = WNDCLASSEXW(ctypes.sizeof(WNDCLASSEXW), 0, WNDPROC(PyWndProcedure), 0,  0, hInst, 0, 0, 0, 0, wintypes.LPCWSTR(wclassName), 0)
regRes = user32.RegisterClassExW(ctypes.byref(wndClass2))
r = wintypes.RECT(0, 0, 800, 450)
user32.AdjustWindowRect(ctypes.byref(r), wintypes.DWORD(0x10C80000),wintypes.BOOL(False))
hwnd = user32.CreateWindowExW(wintypes.DWORD(0), wintypes.LPCWSTR(wclassName), wintypes.LPCWSTR(wname), wintypes.DWORD(0x10CC0000), wintypes.INT(100), wintypes.INT(100), wintypes.INT(r.right - r.left), wintypes.INT(r.bottom - r.top), wintypes.HWND(0), wintypes.HANDLE(0), hInst, wintypes.LPVOID(0))
user32.GetClientRect(hwnd,ctypes.byref(r))
print(r.left, r.top, r.right, r.bottom)
#Creating a DXGI swap chain associated with the window
DXGIFactory = DXGIDevice.GetFactory()
DXGISwapChain = DXGIFactory.CreateSwapChainForHwnd(D3D11Device, hwnd, (0, 0, 'B8G8R8A8_UNORM', False, (1, 0), 'BackBuffer | RenderTargetOutput', 1, 'Stretch', 'Discard', 'Unspecified', 0))
print(DXGISwapChain.GetDesc(), DXGISwapChain.GetFullscreenDesc(), (hwnd, DXGISwapChain.GetHwnd()), )
#Retrieving the DXGI surface from the DXGI swap chain
DXGISurface2 = DXGISwapChain.GetSurface()
#Creating a D2D1 bitmap from the DXGI surface
D2D1Bitmap3 = D2D1DeviceContext.CreateBitmapFromDxgiSurface(DXGISurface2)
#Short way to do the same
# DXGISwapChain, D2D1Bitmap3 = D2D1DeviceContext.CreateSwapChainAndBitmapFromHwnd(hwnd, 'B8G8R8A8_UNORM')
#Setting the D2D1 bitmap as the target of the D2D1 device context
D2D1DeviceContext.SetTarget(D2D1Bitmap3)
#Creating and drawing a D2D1 bitmap from the WIC bitmap
D2D1Bitmap4 = D2D1DeviceContext.CreateBitmapFromWICBitmap(IBitmapCache, {'pixelFormat': ('B8G8R8A8_UNORM', 'premultiplied'), 'colorContext': D2D1ColorContext})
D2D1DeviceContext.SetTarget(D2D1Bitmap3)
D2D1DeviceContext.BeginDraw()
D2D1DeviceContext.Clear((0,0.5,0,1))
D2D1DeviceContext.DrawBitmap(D2D1Bitmap4, (0, 0, *D2D1Bitmap3.GetPixelSize()), 1, 'HighQualityCubic', (0, 0, 1920, 1080))
D2D1DeviceContext.EndDraw()
D2D1DeviceContext.SetTarget()
D2D1Bitmap3.Release()
DXGISurface2.Release()
#Presenting the rendered image of the DXGI swap chain
DXGISwapChain.Present()
#Managing the message queue until the window is closed
print('Waiting for the closure of the resizable pop-up window...')
msg = wintypes.MSG()
lpMsg = ctypes.pointer(msg)
while user32.GetMessageW(lpMsg, hwnd, 0, 0) > 0:
  if msg.message == 16:
    break
  user32.TranslateMessage(lpMsg)
  user32.DispatchMessageW(lpMsg)
user32.DestroyWindow(hwnd)
tuple(map(IUnknown.Release, (IBitmapCache, DXGISurface2, D3D11Texture2D, D3D11Device2, D2D1Bitmap3, D2D1Bitmap4, D2D1Bitmap2, DXGISurface, D2D1Bitmap, D2D1ColorContext, D2D1DeviceContext, D2D1Device, D2D1Factory, DXGIDevice, D3D11Device, DXGISwapChain, DXGIFactory)))

Uninitialize()
