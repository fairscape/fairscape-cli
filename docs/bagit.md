### Packaging an RO-Crate

#### As BagIt

[BagIt](https://datatracker.ietf.org/doc/html/rfc8493) is a file packaging format that allows storing and transferring digital content in a <em>bag</em>. 

```
<base directory>/
         |
         +-- bagit.txt (Required element: Bag Declaration)
         |
         +-- manifest-<algorithm>.txt (Required element: Payload Manifest)
         |
         +-- [additional tag files] (Optional element)
         |
         +-- data/ (Required element: Payload Directory data/)
         |     |
         |     +-- [payload files]
         |
         +-- [tag directories]/ (Optional element)
               |
               +-- [tag files]
```


``` powershell
fairscape-cli rocrate package bagit \
   "/home/sadnan/test_rocrate" \
   "/home/sadnan/test_bagit" \
   --Source-Organization "FOO University" \
   --Organization-Address "1 Main St., Cupertino, California, 11111" \
   --Contact-Name "Jane Doe" \
   --Contact-Phone "+1 111-111-1111" \
   --Contact-Email "example@example.com" \
   --External-Description "Uncompressed greyscale TIFF images from the FOO papers colle..."
```