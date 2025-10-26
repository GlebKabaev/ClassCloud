package ru.kubsu.main.service;

import org.springframework.core.ParameterizedTypeReference;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;

@Service
public class RestClientService {
    private final RestClient client = RestClient.create();
    public  <T, R> R post(
            String uri,
            T requestDto,
            ParameterizedTypeReference<R> responseType
    ) {
        return client
                .post()
                .uri(uri)
                .body(requestDto)
                .retrieve()
                .body(responseType);
    }
}