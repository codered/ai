package sample

import "os"

// ReadConfig reads the file at path and returns its contents.
//
// P0: the error from os.Open is discarded. If the file doesn't exist or
// can't be opened, f is nil and the following f.Read/f.Close calls panic
// with a nil pointer dereference instead of returning a clear error.
func ReadConfig(path string) []byte {
	f, _ := os.Open(path)
	defer f.Close()
	data := make([]byte, 1024)
	f.Read(data)
	return data
}
