#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_PN532.h>

// 手動定義 IRQ 和 RESET 腳位（根據實際接線修改）
#define PN532_IRQ 2   // IRQ 連接到 Arduino D2
#define PN532_RESET 3 // RESET 連接到 Arduino D3

Adafruit_PN532 nfc(PN532_IRQ, PN532_RESET);

void setup(void)
{
    Serial.begin(115200);

    nfc.begin();

    uint32_t versiondata = nfc.getFirmwareVersion();
    if (!versiondata)
    {
        while (1)
            ;
    }

    nfc.SAMConfig();
}

void loop(void)
{
    uint8_t success;
    uint8_t uid[] = {0, 0, 0, 0, 0, 0, 0};
    uint8_t uidLength;

    success = nfc.readPassiveTargetID(PN532_MIFARE_ISO14443A, uid, &uidLength);
    if (success)
    {
        uint64_t uidDecimal = 0;
        String uidStrHex = "";
        for (uint8_t i = 0; i < uidLength; i++)
        {
            uidStrHex += String(uid[i], HEX);
            uidDecimal = uidDecimal * 256 + uid[i];
        }

        String uidDecStr = String((uint32_t)(uidDecimal >> 32)) + String((uint32_t)uidDecimal);

        Serial.println(uidDecStr);
        delay(1000);
    }
    else
    {
    }
}
