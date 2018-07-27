package main

import "bufio"
import "crypto/hmac"
import "crypto/sha256"
import "encoding/base64"
import "fmt"
import "github.com/briandowns/spinner"
import "log"
import "os"
import "os/signal"
import "runtime"
import "syscall"
import "time"

func CheckMAC(message []byte, messageMAC []byte, key []byte) bool {
    mac := hmac.New(sha256.New, key)
    mac.Write(message)
    expectedMAC := mac.Sum(nil)
    return hmac.Equal(messageMAC, expectedMAC)
}

func crack(message []byte, messageMAC []byte, wordfeed <- chan string, hash bool) {
    for {
        word, more := <- wordfeed 

        md := []byte(word)

        // If key should be is sha256(key)
        if hash {
            hash := sha256.New()
            hash.Write([]byte(word))
            md = hash.Sum(nil)
        }

        if more {
            match := CheckMAC(message, messageMAC, md)
            if match {
                fmt.Printf("\n[!] Key found: %s\n", word)
                os.Exit(0)
            }
        }
    }
}

func main() {
    // Print usage
    if len(os.Args) != 4 {
        fmt.Printf("Usage: %s <MESSAGE base64> <HMAC-SHA256 base64> <WORDLIST path>\n", os.Args[0])
        os.Exit(1)
    }

    // Get message, hmac and wordlist path from argv
    var message, err1 = base64.StdEncoding.DecodeString(os.Args[1])
    if err1 != nil {
        fmt.Printf("message must be base64-encoded\n", os.Args[0])
        os.Exit(1)
    }

    var hmac, err2 = base64.StdEncoding.DecodeString(os.Args[1])
    if err2 != nil {
        fmt.Printf("hmac should be in other format\n")
        os.Exit(1)
    }

    var wordlist string = os.Args[3]

    // Terminate when CTRL+C
    c := make(chan os.Signal)
    signal.Notify(c, os.Interrupt, syscall.SIGTERM)
    go func() {
        sig := <-c
        fmt.Printf("\n[*] Signal %d received - exiting\n", sig)
        os.Exit(1)
    }()

    // Create a progress indicator & one go-routine per CPU?
    s := spinner.New(spinner.CharSets[9], 100*time.Millisecond)
    s.Prefix = "["

    var numCPU int = runtime.NumCPU()*2
    if numCPU == 1 {
        s.Suffix = fmt.Sprintf("] Cracking (%d thread)", numCPU)
    } else {
        s.Suffix = fmt.Sprintf("] Cracking (%d threads)", numCPU)
    }
    s.Start()

    words := make(chan string)
    for i := 0; i < runtime.NumCPU(); i++ {
        go crack(message, hmac, words, false)
    }

    // Feed cracker go-routines with words
    file, err := os.Open(wordlist)
    if err != nil {
        log.Fatal(err)
    }
    defer file.Close()

    scanner := bufio.NewScanner(file)
    for scanner.Scan() {
        words <- scanner.Text()
    }
    if err := scanner.Err(); err != nil {
        log.Fatal(err)
    }

    // End
    close(words)
    s.Prefix = ""
    s.Suffix = ""
    s.Stop()
    fmt.Printf("[?] Exhausted                           \n")
    os.Exit(0)
}
