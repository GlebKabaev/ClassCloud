package ru.kubsu.main.config;

import io.minio.MinioClient;
import io.minio.MakeBucketArgs;
import io.minio.BucketExistsArgs;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import lombok.extern.slf4j.Slf4j;

@Configuration
@Slf4j
public class MinioConfig {
    private final String endpoint;
    private final String accessKey;
    private final String secretKey;
    private final String bucketName;

    public MinioConfig(@Value("${minio.endpoint}") String endpoint,
                       @Value("${minio.access-key}") String accessKey,
                       @Value("${minio.secret-key}") String secretKey,
                       @Value("${minio.bucket-name}") String bucketName) {
        this.endpoint = endpoint;
        this.accessKey = accessKey;
        this.secretKey = secretKey;
        this.bucketName = bucketName;
    }

    @Bean
    public MinioClient createClient() {

        MinioClient minioClient = MinioClient.builder()
                .endpoint(endpoint)
                .credentials(accessKey, secretKey)
                .build();
        try {
            ensureBucketExists(minioClient, bucketName);
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
        return minioClient;
    }

    public static void ensureBucketExists(MinioClient client, String bucketName) throws Exception {
        boolean found = client.bucketExists(BucketExistsArgs.builder().bucket(bucketName).build());
        if (!found) {
            client.makeBucket(MakeBucketArgs.builder().bucket(bucketName).build());
            log.info("✅ Создан бакет: {}", bucketName);
        } else {
            log.info("ℹ️ Бакет уже существует: {}", bucketName);
        }
    }
}
